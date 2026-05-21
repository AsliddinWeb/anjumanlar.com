"""Order lifecycle coverage.

Hits the service layer directly for the state-machine maths (price
snapshot, commission split, expiration sweep) and the HTTP layer for
the auth+ownership rules.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import (
    AuthorProfile,
    Book,
    BookLanguage,
    BookStatus,
    Order,
    OrderStatus,
    User,
    UserLibrary,
    UserRole,
    UserStatus,
)
from app.services import order_service

PW = "Hunter22!"


# ---------- helpers ----------


async def _make_user(db: AsyncSession, email: str, role: UserRole = UserRole.reader) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name=email.split("@")[0],
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


async def _make_book(
    db: AsyncSession,
    slug: str,
    *,
    price: float = 10000,
    discount: float | None = None,
    commission: float = 15,
) -> Book:
    author_user = await _make_user(db, f"author-{slug}@example.com", UserRole.author)
    profile = AuthorProfile(
        user_id=author_user.id,
        slug=f"prof-{slug}",
        display_name=f"Author {slug}",
        commission_rate=commission,
    )
    db.add(profile)
    await db.flush()
    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug=slug,
        title={"uz": f"Kitob {slug}"},
        language=BookLanguage.uz,
        price=price,
        discount_price=discount,
        status=BookStatus.approved,
        published_at=datetime.now(UTC),
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- service-level: price snapshot ----------


@pytest.mark.asyncio
async def test_create_order_snapshots_price_and_commission(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-snapshot@example.com")
    book = await _make_book(db_session, "snap", price=50000, commission=15)

    order = await order_service.create_order(db_session, user, [book.id])
    assert order.status == OrderStatus.pending
    assert order.subtotal == 50000
    assert order.total == 50000
    assert order.expires_at is not None
    assert order.expires_at > datetime.now(UTC)

    assert len(order.items) == 1
    item = order.items[0]
    assert float(item.price) == 50000
    assert float(item.commission_rate) == 15
    assert float(item.author_earning) == 42500  # 50000 * 0.85
    assert float(item.platform_fee) == 7500


@pytest.mark.asyncio
async def test_create_order_uses_discount_when_lower(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-discount@example.com")
    book = await _make_book(db_session, "disc", price=80000, discount=60000)

    order = await order_service.create_order(db_session, user, [book.id])
    assert order.items[0].price == 60000
    assert order.subtotal == 60000


@pytest.mark.asyncio
async def test_create_order_assigns_unique_order_number(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-num@example.com")
    book = await _make_book(db_session, "num")
    book2 = await _make_book(db_session, "num2")

    a = await order_service.create_order(db_session, user, [book.id])
    b = await order_service.create_order(db_session, user, [book2.id])

    assert a.order_number != b.order_number
    assert a.order_number.startswith("ANJ-")
    assert b.order_number.startswith("ANJ-")


# ---------- service-level: validation ----------


@pytest.mark.asyncio
async def test_create_order_rejects_unknown_book(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-404@example.com")
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await order_service.create_order(
            db_session,
            user,
            [__import__("uuid").UUID("00000000-0000-0000-0000-000000000000")],
        )


@pytest.mark.asyncio
async def test_create_order_rejects_already_owned_book(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-owned@example.com")
    book = await _make_book(db_session, "owned")

    # Pretend the user already bought it.
    db_session.add(UserLibrary(user_id=user.id, book_id=book.id))
    await db_session.flush()

    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await order_service.create_order(db_session, user, [book.id])


# ---------- service-level: state machine ----------


@pytest.mark.asyncio
async def test_cancel_pending_order(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-cancel@example.com")
    book = await _make_book(db_session, "cancel")
    order = await order_service.create_order(db_session, user, [book.id])

    cancelled = await order_service.cancel(db_session, user, order.id)
    assert cancelled.status == OrderStatus.cancelled


@pytest.mark.asyncio
async def test_cannot_cancel_paid_order(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-paid@example.com")
    book = await _make_book(db_session, "paid")
    order = await order_service.create_order(db_session, user, [book.id])

    await order_service.mark_paid(db_session, order)
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await order_service.cancel(db_session, user, order.id)


@pytest.mark.asyncio
async def test_expire_stale_flips_pending_past_deadline(db_session: AsyncSession):
    user = await _make_user(db_session, "buyer-expire@example.com")
    book_a = await _make_book(db_session, "exp-a")
    book_b = await _make_book(db_session, "exp-b")

    expired_order = await order_service.create_order(db_session, user, [book_a.id])
    fresh_order = await order_service.create_order(db_session, user, [book_b.id])

    # Backdate one of the orders so it's past its TTL.
    expired_order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.flush()

    count = await order_service.expire_stale(db_session)
    assert count == 1

    await db_session.refresh(expired_order)
    await db_session.refresh(fresh_order)
    assert expired_order.status == OrderStatus.expired
    assert fresh_order.status == OrderStatus.pending


# ---------- HTTP layer: auth + ownership ----------


@pytest.mark.asyncio
async def test_post_orders_requires_auth(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_book(db_session, "anon-order")
    resp = await api_client.post("/api/v1/orders", json={"book_ids": [str(book.id)]})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_orders_happy_path(api_client: AsyncClient, db_session: AsyncSession):
    user = await _make_user(db_session, "http-buyer@example.com")
    book = await _make_book(db_session, "http-buy", price=20000)
    token = await _token(api_client, user.email)

    resp = await api_client.post(
        "/api/v1/orders",
        headers=_h(token),
        json={"book_ids": [str(book.id)]},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["payment_url"] is None
    order = body["order"]
    assert order["status"] == "pending"
    assert order["total"] == 20000
    assert len(order["items"]) == 1


@pytest.mark.asyncio
async def test_get_order_forbidden_for_other_user(
    api_client: AsyncClient, db_session: AsyncSession
):
    owner = await _make_user(db_session, "order-owner@example.com")
    other = await _make_user(db_session, "order-other@example.com")
    book = await _make_book(db_session, "owner-book")

    order = await order_service.create_order(db_session, owner, [book.id])
    await db_session.commit()

    other_token = await _token(api_client, other.email)
    resp = await api_client.get(f"/api/v1/orders/{order.id}", headers=_h(other_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_read_any_order(api_client: AsyncClient, db_session: AsyncSession):
    owner = await _make_user(db_session, "owner-for-admin@example.com")
    admin = await _make_user(db_session, "admin-orders@example.com", role=UserRole.admin)
    book = await _make_book(db_session, "admin-readable")

    order = await order_service.create_order(db_session, owner, [book.id])
    await db_session.commit()

    admin_token = await _token(api_client, admin.email)
    resp = await api_client.get(f"/api/v1/orders/{order.id}", headers=_h(admin_token))
    assert resp.status_code == 200
    assert resp.json()["order_number"] == order.order_number
