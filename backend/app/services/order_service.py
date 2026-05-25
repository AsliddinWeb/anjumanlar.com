"""Order lifecycle.

State machine::

    pending ──pay──> paid ──refund (later)──> refunded
       │
       ├── expires_at hit ──> expired   (celery beat)
       └── owner cancels ───> cancelled (POST /orders/{id}/cancel)

Pricing is snapshotted at order-item time from the authoritative
``Book`` row, so a price change after the buyer hits "Buy" doesn't
move the goalposts mid-checkout. ``commission_rate`` is captured from
the author profile for the same reason — retroactive rate changes
shouldn't reshuffle past payouts.

The service never commits. Callers (endpoints, celery tasks) own the
transaction so cross-cutting concerns (audit, email, balance update)
can stay atomic with the state change.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Book,
    BookStatus,
    Order,
    OrderItem,
    OrderStatus,
    User,
    UserLibrary,
    UserRole,
)

# Pending orders are reserved for half an hour; after that the celery
# beat job marks them ``expired`` so the user (or staff) sees a clean
# state rather than a forever-pending invoice.
PENDING_TTL = timedelta(minutes=30)

# Order numbers look like ``ANJ-2026-000123`` — the ``orders_seq``
# Postgres sequence supplies a process-safe counter; the year prefix
# is cosmetic (cross-year continuity is fine since the column is
# unique on its own).
ORDER_NUMBER_PREFIX = "ANJ"


def _format_order_number(seq: int, year: int | None = None) -> str:
    year = year or datetime.now(UTC).year
    return f"{ORDER_NUMBER_PREFIX}-{year}-{seq:06d}"


async def _next_order_number(db: AsyncSession) -> str:
    seq = (await db.execute(select(func.nextval("orders_seq")))).scalar_one()
    return _format_order_number(int(seq))


async def _fetch_books(db: AsyncSession, book_ids: list[UUID]) -> list[Book]:
    """Load only purchasable books — approved + not soft-deleted.

    Eagerly pulls the author so commission_rate is available without a
    second round-trip per item.
    """
    if not book_ids:
        raise ValidationError("at least one book is required")

    # Drop duplicates while preserving order; we use the set for lookup.
    unique_ids = list(dict.fromkeys(book_ids))
    rows = (
        (
            await db.execute(
                select(Book)
                .options(selectinload(Book.author))
                .where(
                    Book.id.in_(unique_ids),
                    Book.status == BookStatus.approved,
                )
            )
        )
        .scalars()
        .unique()
        .all()
    )
    by_id = {b.id: b for b in rows}
    missing = [bid for bid in unique_ids if bid not in by_id]
    if missing:
        raise NotFoundError(
            "One or more books are unavailable",
            details={"code": "book_unavailable", "book_ids": [str(m) for m in missing]},
        )
    return [by_id[bid] for bid in unique_ids]


async def _already_owned(
    db: AsyncSession, user: User, book_ids: list[UUID]
) -> list[UUID]:
    rows = (
        await db.execute(
            select(UserLibrary.book_id).where(
                UserLibrary.user_id == user.id,
                UserLibrary.book_id.in_(book_ids),
            )
        )
    ).scalars().all()
    return list(rows)


def _line_amounts(book: Book) -> tuple[float, float, float, float]:
    """Compute (price, commission_rate, author_earning, platform_fee) for one item.

    Uses ``discount_price`` if set and lower than the headline price.
    """
    base = float(book.price)
    if book.discount_price is not None and 0 < float(book.discount_price) < base:
        price = float(book.discount_price)
    else:
        price = base

    rate = float(book.author.commission_rate)
    platform_fee = round(price * rate / 100, 2)
    author_earning = round(price - platform_fee, 2)
    return price, rate, author_earning, platform_fee


async def create_order(
    db: AsyncSession,
    user: User,
    book_ids: list[UUID],
    *,
    payment_method: str | None = "payme",
) -> Order:
    """Build a pending Order + OrderItem rows for a basket of books."""

    books = await _fetch_books(db, book_ids)

    owned = await _already_owned(db, user, [b.id for b in books])
    if owned:
        raise ConflictError(
            "You already own one or more of these books",
            details={"code": "already_owned", "book_ids": [str(b) for b in owned]},
        )

    subtotal = 0.0
    items: list[OrderItem] = []
    for book in books:
        price, rate, author_earning, platform_fee = _line_amounts(book)
        items.append(
            OrderItem(
                book_id=book.id,
                price=price,
                commission_rate=rate,
                author_earning=author_earning,
                platform_fee=platform_fee,
            )
        )
        subtotal += price

    order_number = await _next_order_number(db)
    order = Order(
        order_number=order_number,
        user_id=user.id,
        status=OrderStatus.pending,
        subtotal=subtotal,
        discount=0,
        total=subtotal,
        currency="UZS",
        payment_method=payment_method,
        expires_at=datetime.now(UTC) + PENDING_TTL,
        items=items,
    )
    db.add(order)

    try:
        await db.flush()
    except IntegrityError as exc:  # extremely unlikely — sequence collision
        raise ConflictError("Could not assign an order number — retry") from exc

    return await get_with_items(db, order.id)


async def get_with_items(db: AsyncSession, order_id: UUID) -> Order:
    row = (
        await db.execute(
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.book)
                .selectinload(Book.author),
                selectinload(Order.items)
                .selectinload(OrderItem.book)
                .selectinload(Book.categories),
            )
            .where(Order.id == order_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Order not found", details={"code": "order_not_found"})
    return row


async def get_for_user(db: AsyncSession, user: User, order_id: UUID) -> Order:
    order = await get_with_items(db, order_id)
    if order.user_id != user.id and user.role not in (UserRole.admin, UserRole.superadmin):
        raise ForbiddenError(
            "You don't have access to this order", details={"code": "order_forbidden"}
        )
    return order


async def list_for_user(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
    status: OrderStatus | None = None,
) -> tuple[list[Order], int]:
    base = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.book)
            .selectinload(Book.author),
            selectinload(Order.items)
            .selectinload(OrderItem.book)
            .selectinload(Book.categories),
        )
        .where(Order.user_id == user.id)
    )
    if status is not None:
        base = base.where(Order.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(Order.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def cancel(db: AsyncSession, user: User, order_id: UUID) -> Order:
    order = await get_for_user(db, user, order_id)
    if order.status != OrderStatus.pending:
        raise ConflictError(
            "Only pending orders can be cancelled",
            details={"code": "invalid_state", "current_status": order.status.value},
        )
    order.status = OrderStatus.cancelled
    await db.flush()
    return order


async def mark_paid(db: AsyncSession, order: Order) -> Order:
    """Caller is the payment-webhook handler — flips state + paid_at."""
    if order.status not in (OrderStatus.pending, OrderStatus.failed):
        raise ConflictError(
            "Order cannot be marked paid from its current state",
            details={"code": "invalid_state", "current_status": order.status.value},
        )
    order.status = OrderStatus.paid
    order.paid_at = datetime.now(UTC)
    await db.flush()
    return order


async def mark_failed(db: AsyncSession, order: Order) -> Order:
    if order.status != OrderStatus.pending:
        raise ConflictError(
            "Only pending orders can be marked failed",
            details={"code": "invalid_state", "current_status": order.status.value},
        )
    order.status = OrderStatus.failed
    await db.flush()
    return order


async def expire_stale(db: AsyncSession, *, now: datetime | None = None) -> int:
    """Flip any ``pending`` order past its ``expires_at`` to ``expired``.

    Returns the number of orders moved. Called from the celery beat
    job; safe to invoke from tests too.
    """
    cutoff = now or datetime.now(UTC)
    stale = (
        (
            await db.execute(
                select(Order).where(
                    Order.status == OrderStatus.pending,
                    Order.expires_at.is_not(None),
                    Order.expires_at <= cutoff,
                )
            )
        )
        .scalars()
        .all()
    )
    for order in stale:
        order.status = OrderStatus.expired
    if stale:
        await db.flush()
    return len(stale)
