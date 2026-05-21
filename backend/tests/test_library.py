"""Library + post-purchase fan-out coverage.

Exercises :func:`library_service.grant_order` directly (so we can drive
the state without spinning up Payme) plus the HTTP layer for list +
download endpoints. Celery enqueues are intercepted via monkeypatch.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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
    OrderStatus,
    User,
    UserLibrary,
    UserRole,
    UserStatus,
)
from app.services import library_service, order_service

PW = "Hunter22!"


@pytest.fixture
def captured_watermarks(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    calls: list[tuple[str, str, str]] = []

    def fake_delay(book_id: str, user_id: str, text: str) -> object:
        calls.append((book_id, user_id, text))

        class _R:
            id = "fake"

        return _R()

    monkeypatch.setattr("app.tasks.pdf_tasks.watermark_pdf.delay", fake_delay)
    return calls


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_delay(**kwargs):
        calls.append(kwargs)

        class _R:
            id = "fake"

        return _R()

    monkeypatch.setattr("app.tasks.email_tasks.send_template_email.delay", fake_delay)
    return calls


async def _make_user(db: AsyncSession, email: str) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name=email.split("@")[0],
        role=UserRole.reader,
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
    price: float = 50000,
    commission: float = 15,
) -> Book:
    author_user = User(
        email=f"author-{slug}@example.com",
        password_hash=hash_password(PW),
        full_name=f"Author {slug}",
        role=UserRole.author,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(author_user)
    await db.flush()
    profile = AuthorProfile(
        user_id=author_user.id,
        slug=f"prof-{slug}",
        display_name=f"Prof {slug}",
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
        status=BookStatus.approved,
        published_at=datetime.now(UTC),
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book, profile


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- grant_order ----------


@pytest.mark.asyncio
async def test_grant_order_creates_library_rows_and_bumps_balance(
    db_session: AsyncSession,
    captured_watermarks: list[tuple[str, str, str]],
    captured_emails: list[dict[str, Any]],
):
    user = await _make_user(db_session, "grant-buyer@example.com")
    book, author = await _make_book(db_session, "grant-book", price=80000, commission=15)
    starting_balance = float(author.available_balance)

    order = await order_service.create_order(db_session, user, [book.id])
    await order_service.mark_paid(db_session, order)

    new_rows = await library_service.grant_order(db_session, order)
    assert len(new_rows) == 1

    library_rows = (
        await db_session.execute(select(UserLibrary).where(UserLibrary.user_id == user.id))
    ).scalars().all()
    assert len(library_rows) == 1
    assert library_rows[0].book_id == book.id
    assert library_rows[0].order_id == order.id

    await db_session.refresh(author)
    assert float(author.available_balance) == starting_balance + 68000  # 80000 * 0.85
    assert float(author.total_revenue) == 68000
    assert author.total_sales == 1

    assert len(captured_watermarks) == 1
    book_id_str, user_id_str, text = captured_watermarks[0]
    assert book_id_str == str(book.id)
    assert user_id_str == str(user.id)
    assert user.email in text

    assert len(captured_emails) == 1
    assert captured_emails[0]["template_name"] == "library_grant"
    assert captured_emails[0]["context"]["order_number"] == order.order_number


@pytest.mark.asyncio
async def test_grant_order_is_idempotent(
    db_session: AsyncSession,
    captured_watermarks: list[tuple[str, str, str]],
    captured_emails: list[dict[str, Any]],
):
    user = await _make_user(db_session, "idem-buyer@example.com")
    book, _ = await _make_book(db_session, "idem-book")
    order = await order_service.create_order(db_session, user, [book.id])
    await order_service.mark_paid(db_session, order)

    first = await library_service.grant_order(db_session, order)
    second = await library_service.grant_order(db_session, order)
    assert len(first) == 1
    assert second == []

    rows = (
        await db_session.execute(select(UserLibrary).where(UserLibrary.user_id == user.id))
    ).scalars().all()
    assert len(rows) == 1

    # Side effects fire only on the first grant.
    assert len(captured_watermarks) == 1
    assert len(captured_emails) == 1


@pytest.mark.asyncio
async def test_grant_order_aggregates_balance_per_author(
    db_session: AsyncSession,
    captured_watermarks: list[tuple[str, str, str]],
    captured_emails: list[dict[str, Any]],
):
    """Two books from the same author in one order should bump the
    author balance with the *sum* of both line earnings."""
    user = await _make_user(db_session, "multi-buyer@example.com")
    book_a, author = await _make_book(db_session, "multi-a", price=60000)

    # Reuse the same author profile for the second book.
    book_b = Book(
        author_id=author.id,
        uploaded_by=author.user_id,
        slug="multi-b",
        title={"uz": "Kitob multi-b"},
        language=BookLanguage.uz,
        price=40000,
        status=BookStatus.approved,
        published_at=datetime.now(UTC),
    )
    db_session.add(book_b)
    await db_session.flush()
    await db_session.refresh(book_b)

    order = await order_service.create_order(db_session, user, [book_a.id, book_b.id])
    await order_service.mark_paid(db_session, order)
    await library_service.grant_order(db_session, order)

    await db_session.refresh(author)
    # 60000 * 0.85 + 40000 * 0.85 = 51000 + 34000 = 85000
    assert float(author.available_balance) == 85000


@pytest.mark.asyncio
async def test_grant_order_rejects_unpaid_order(db_session: AsyncSession):
    user = await _make_user(db_session, "unpaid-buyer@example.com")
    book, _ = await _make_book(db_session, "unpaid-book")
    order = await order_service.create_order(db_session, user, [book.id])

    with pytest.raises(ValueError):
        await library_service.grant_order(db_session, order)


# ---------- HTTP layer ----------


@pytest.mark.asyncio
async def test_list_library_returns_owned_books(
    api_client: AsyncClient,
    db_session: AsyncSession,
    captured_watermarks: list[tuple[str, str, str]],
    captured_emails: list[dict[str, Any]],
):
    user = await _make_user(db_session, "lib-list@example.com")
    book, _ = await _make_book(db_session, "lib-list-book")
    order = await order_service.create_order(db_session, user, [book.id])
    await order_service.mark_paid(db_session, order)
    await library_service.grant_order(db_session, order)
    await db_session.commit()

    token = await _token(api_client, user.email)
    resp = await api_client.get("/api/v1/libraries/me", headers=_h(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["book"]["slug"] == "lib-list-book"


@pytest.mark.asyncio
async def test_download_requires_ownership(api_client: AsyncClient, db_session: AsyncSession):
    owner = await _make_user(db_session, "owner-download@example.com")
    stranger = await _make_user(db_session, "stranger-download@example.com")
    book, _ = await _make_book(db_session, "owned-only")

    db_session.add(UserLibrary(user_id=owner.id, book_id=book.id))
    await db_session.flush()
    await db_session.commit()

    stranger_token = await _token(api_client, stranger.email)
    resp = await api_client.get(
        f"/api/v1/libraries/me/{book.id}/download",
        headers=_h(stranger_token),
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["details"]["code"] == "not_in_library"
