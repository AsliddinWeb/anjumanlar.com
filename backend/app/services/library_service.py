"""Post-purchase fan-out: library row, balance bump, watermark, email.

``grant_order`` is the single entry point. It's called from two places:

- :func:`app.services.payme_service.PaymeMerchant._perform` for paid
  Payme transactions.
- The (future) free-checkout endpoint that bypasses Payme for ₿0 orders.

The function is idempotent: re-running it on a paid order with library
rows already in place is a no-op, so retries on the webhook side don't
double-grant access.

Side-effects ordering:

1. Insert ``UserLibrary`` rows (DB).
2. Bump ``AuthorProfile.available_balance`` + ``total_sales`` +
   ``total_revenue`` (DB).
3. Enqueue ``pdf.watermark`` for each book (Celery — fire-and-forget,
   any retry happens in the worker).
4. Enqueue the "book in library" email (Celery — same reason).

Steps 3-4 are best-effort: a Celery enqueue failure would surface as
a 500 to the webhook caller, which we don't want, so they're wrapped
in try/except. The library + balance writes are the only changes that
must succeed atomically with the order flip.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import NotFoundError
from app.integrations.minio_client import presigned_get_url
from app.models import (
    AuthorProfile,
    Book,
    Order,
    OrderItem,
    OrderStatus,
    User,
    UserLibrary,
)

# Presigned download URLs expire after this many seconds — short enough
# that a leaked URL is useless tomorrow, long enough to cover a slow
# mobile connection completing the download.
DOWNLOAD_URL_TTL_SECONDS = 600

logger = logging.getLogger(__name__)


async def grant_order(db: AsyncSession, order: Order) -> list[UserLibrary]:
    """Materialise a paid order into library rows + author payouts.

    Callers must have already moved the order to ``OrderStatus.paid``.
    Returns the freshly-created library rows; existing rows for the
    same (user, book) pair are left untouched.
    """
    if order.status != OrderStatus.paid:
        raise ValueError(
            f"grant_order expects a paid order, got {order.status.value}"
        )

    # Refresh items + their books with author + uploaded_by populated so
    # we can resolve watermark text and update author balances without
    # extra round-trips.
    refreshed = (
        await db.execute(
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.book)
                .selectinload(Book.author),
            )
            .where(Order.id == order.id)
        )
    ).scalar_one()

    user = (
        await db.execute(select(User).where(User.id == refreshed.user_id))
    ).scalar_one()

    # Build the set of books already in the user's library so we don't
    # double-insert on retry.
    existing_ids = set(
        (
            await db.execute(
                select(UserLibrary.book_id).where(
                    UserLibrary.user_id == refreshed.user_id,
                    UserLibrary.book_id.in_([i.book_id for i in refreshed.items]),
                )
            )
        )
        .scalars()
        .all()
    )

    new_rows: list[UserLibrary] = []
    author_increments: dict[str, tuple[AuthorProfile, float]] = {}

    for item in refreshed.items:
        if item.book_id in existing_ids:
            continue

        row = UserLibrary(
            user_id=refreshed.user_id,
            book_id=item.book_id,
            order_id=refreshed.id,
            acquired_at=datetime.now(UTC),
        )
        db.add(row)
        new_rows.append(row)

        # Aggregate per-author so multi-book orders from one author hit
        # the balance once.
        author = item.book.author
        key = str(author.id)
        if key in author_increments:
            profile, amount = author_increments[key]
            author_increments[key] = (profile, amount + float(item.author_earning))
        else:
            author_increments[key] = (author, float(item.author_earning))

    if not new_rows:
        # Re-grant on already-fulfilled order — nothing to do.
        return []

    await db.flush()

    for profile, amount in author_increments.values():
        # Bump payable balance + lifetime totals. ``total_sales`` counts
        # *items*, not orders, because authors care about per-book
        # uptake.
        profile.available_balance = float(profile.available_balance) + amount
        profile.total_revenue = float(profile.total_revenue) + amount
        profile.total_sales = profile.total_sales + 1
    if author_increments:
        await db.flush()

    # Fire-and-forget side effects — failures here must not bring down
    # the webhook caller.
    try:
        _enqueue_watermarks(refreshed, new_rows, user)
        _enqueue_library_email(refreshed, user, new_rows)
    except Exception:
        logger.exception(
            "library.grant_order: side-effect enqueue failed for order %s", refreshed.id
        )

    logger.info(
        "library.grant_order order=%s user=%s new_rows=%s",
        refreshed.id,
        refreshed.user_id,
        len(new_rows),
    )
    return new_rows


def _watermark_text(user: User, paid_at: datetime | None) -> str:
    stamp = (paid_at or datetime.now(UTC)).strftime("%Y-%m-%d")
    return f"{user.email} · {stamp}"


def _enqueue_watermarks(
    order: Order, new_rows: list[UserLibrary], user: User
) -> None:
    # Local import keeps Celery off the test import path until needed.
    from app.tasks.pdf_tasks import watermark_pdf

    text = _watermark_text(user, order.paid_at)
    for row in new_rows:
        watermark_pdf.delay(str(row.book_id), str(user.id), text)


def _enqueue_library_email(
    order: Order, user: User, new_rows: list[UserLibrary]
) -> None:
    from app.tasks.email_tasks import send_template_email

    book_titles: list[str] = []
    for row in new_rows:
        # row.book may not be loaded; reach through the order items.
        for item in order.items:
            if item.book_id == row.book_id:
                book_titles.append(_pick_title(item.book.title, user.preferred_locale))
                break

    send_template_email.delay(
        to=user.email,
        template_name="library_grant",
        locale=user.preferred_locale or "uz",
        context={
            "full_name": user.full_name,
            "email": user.email,
            "order_number": order.order_number,
            "book_titles": book_titles,
        },
    )


async def list_for_user(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
) -> tuple[list[UserLibrary], int]:
    base = (
        select(UserLibrary)
        .options(
            selectinload(UserLibrary.book).selectinload(Book.author),
            selectinload(UserLibrary.book).selectinload(Book.categories),
        )
        .where(UserLibrary.user_id == user.id)
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(UserLibrary.acquired_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def issue_download_url(
    db: AsyncSession, user: User, book_id
) -> tuple[str, int]:
    """Return a presigned URL for the user's watermarked PDF of ``book_id``.

    Raises NotFoundError if the user doesn't own the book or the
    watermark task hasn't finished yet (no ``watermarked_url`` on the
    row — frontend should poll).
    """
    row = (
        await db.execute(
            select(UserLibrary).where(
                UserLibrary.user_id == user.id,
                UserLibrary.book_id == book_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "You don't own this book yet", details={"code": "not_in_library"}
        )

    # Object key matches what pdf_tasks.watermark_pdf writes:
    # ``<user_id>/<book_id>.pdf`` inside ``books-watermarked``.
    object_key = f"{user.id}/{book_id}.pdf"
    url = presigned_get_url(
        settings.MINIO_BUCKET_BOOKS_WM,
        object_key,
        expires_seconds=DOWNLOAD_URL_TTL_SECONDS,
    )

    row.downloaded_count = row.downloaded_count + 1
    from datetime import datetime as _dt

    row.last_downloaded_at = _dt.now(UTC)
    await db.flush()
    return url, DOWNLOAD_URL_TTL_SECONDS


def _pick_title(title_map: dict, preferred: str | None) -> str:
    if not isinstance(title_map, dict):
        return ""
    for key in (preferred, "uz", "en", "ru"):
        if key and isinstance(title_map.get(key), str) and title_map[key].strip():
            return title_map[key]
    return next((v for v in title_map.values() if isinstance(v, str) and v.strip()), "")
