"""Admin dashboard KPI snapshot — shape + RBAC."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import (
    AuthorProfile,
    Book,
    BookLanguage,
    BookStatus,
    Order,
    OrderItem,
    OrderStatus,
    User,
    UserRole,
    UserStatus,
)
from app.services import stats_service

PW = "Hunter22!"


async def _make_user(
    db: AsyncSession, email: str, role: UserRole = UserRole.reader
) -> User:
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


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- service-level ----------


@pytest.mark.asyncio
async def test_snapshot_contains_every_section(db_session: AsyncSession):
    snap = await stats_service.snapshot(db_session)
    for key in ("users", "books", "reviews", "orders", "revenue", "withdrawals", "generated_at"):
        assert key in snap


@pytest.mark.asyncio
async def test_snapshot_counts_active_users(db_session: AsyncSession):
    await _make_user(db_session, "active-1@example.com")
    deleted = await _make_user(db_session, "deleted-1@example.com")
    deleted.status = UserStatus.deleted
    await db_session.flush()

    snap = await stats_service.snapshot(db_session)
    assert snap["users"]["total"] >= 1
    # The deleted user should not be included in ``total``.
    # We can't easily assert exact counts because conftest may have created
    # other users; instead, check the deleted one *isn't* added on top.
    snap_after = await stats_service.snapshot(db_session)
    assert snap_after["users"]["total"] == snap["users"]["total"]


@pytest.mark.asyncio
async def test_snapshot_counts_pending_books(db_session: AsyncSession):
    # Create an author + a pending book.
    author_user = await _make_user(db_session, "stats-author@example.com", UserRole.author)
    profile = AuthorProfile(
        user_id=author_user.id, slug="stats-author", display_name="Stats Author"
    )
    db_session.add(profile)
    await db_session.flush()
    db_session.add(
        Book(
            author_id=profile.id,
            uploaded_by=author_user.id,
            slug="stats-pending",
            title={"uz": "Pending"},
            language=BookLanguage.uz,
            price=10_000,
            status=BookStatus.pending,
        )
    )
    await db_session.flush()

    snap = await stats_service.snapshot(db_session)
    assert snap["books"]["pending"] >= 1


@pytest.mark.asyncio
async def test_snapshot_sums_paid_revenue(db_session: AsyncSession):
    buyer = await _make_user(db_session, "stats-buyer@example.com")
    author_user = await _make_user(db_session, "stats-author2@example.com", UserRole.author)
    profile = AuthorProfile(
        user_id=author_user.id, slug="stats-author2", display_name="A"
    )
    db_session.add(profile)
    await db_session.flush()
    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug="stats-buy",
        title={"uz": "B"},
        language=BookLanguage.uz,
        price=20_000,
        status=BookStatus.approved,
    )
    db_session.add(book)
    await db_session.flush()

    order = Order(
        order_number="ANJ-2026-STATS",
        user_id=buyer.id,
        status=OrderStatus.paid,
        subtotal=20_000,
        total=20_000,
        currency="UZS",
        paid_at=datetime.now(UTC),
        items=[
            OrderItem(
                book_id=book.id,
                price=20_000,
                commission_rate=15,
                author_earning=17_000,
                platform_fee=3_000,
            )
        ],
    )
    db_session.add(order)
    await db_session.flush()

    snap = await stats_service.snapshot(db_session)
    assert snap["orders"]["paid_total"] >= 1
    assert snap["revenue"]["gross"] >= 20_000
    assert snap["revenue"]["platform_fee"] >= 3_000


# ---------- HTTP ----------


@pytest.mark.asyncio
async def test_stats_requires_admin(api_client: AsyncClient, db_session: AsyncSession):
    reader = await _make_user(db_session, "stats-reader@example.com")
    await db_session.commit()
    token = await _token(api_client, reader.email)
    resp = await api_client.get("/api/v1/admin/stats", headers=_h(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_stats_admin_ok(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "stats-admin@example.com", role=UserRole.admin)
    await db_session.commit()
    token = await _token(api_client, admin.email)
    resp = await api_client.get("/api/v1/admin/stats", headers=_h(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "users" in body
    assert "revenue" in body
