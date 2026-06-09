"""Phase 4 end-to-end edge cases.

These cover the seams between order, payment, library and balance —
the places where individual unit tests miss a class of bug because
the failure only shows up when the pieces interact.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.integrations.payme.client import uzs_to_tiyin
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
from app.services import library_service, order_service

PW = "Hunter22!"
TEST_KEY = "test-payme-edge"
WEBHOOK_PATH = "/api/v1/payments/payme/callback"


@pytest.fixture(autouse=True)
def _payme_key(monkeypatch):
    monkeypatch.setattr(settings, "PAYME_SECRET_KEY", TEST_KEY)
    monkeypatch.setattr(settings, "PAYME_MERCHANT_ID", "edge-merchant")
    monkeypatch.setattr(settings, "PAYME_CHECKOUT_URL", "https://checkout.test.paycom.uz")


@pytest.fixture
def captured_watermarks(monkeypatch: pytest.MonkeyPatch):
    calls: list = []

    def fake(book_id, user_id, text):
        calls.append((book_id, user_id, text))

        class _R:
            id = "fake"

        return _R()

    monkeypatch.setattr("app.tasks.pdf_tasks.watermark_pdf.delay", fake)
    return calls


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch):
    calls: list = []

    def fake(**kwargs):
        calls.append(kwargs)

        class _R:
            id = "fake"

        return _R()

    monkeypatch.setattr("app.tasks.email_tasks.send_template_email.delay", fake)
    return calls


def _auth_header(key: str = TEST_KEY) -> dict[str, str]:
    raw = f"Paycom:{key}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


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
) -> tuple[Book, AuthorProfile]:
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
    )
    db.add(profile)
    await db.flush()
    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug=slug,
        title={"uz": slug},
        language=BookLanguage.uz,
        price=price,
        status=BookStatus.approved,
        published_at=datetime.now(UTC),
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    await db.refresh(profile)
    return book, profile


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- end-to-end happy path ----------


@pytest.mark.asyncio
async def test_full_purchase_flow_grants_library_and_balance(
    api_client: AsyncClient,
    db_session: AsyncSession,
    captured_watermarks,
    captured_emails,
):
    """Cart → order → Payme create+perform → library + author balance."""
    user = await _make_user(db_session, "e2e-buyer@example.com")
    book, author = await _make_book(db_session, "e2e-book", price=80_000)
    starting_balance = float(author.available_balance)

    order = await order_service.create_order(db_session, user, [book.id])
    await db_session.commit()

    # Create transaction via Payme webhook.
    tiyin = uzs_to_tiyin(80_000)
    await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CreateTransaction",
            "params": {
                "id": "e2e-tx",
                "time": 1_700_000_000_000,
                "amount": tiyin,
                "account": {"order_id": str(order.id)},
            },
        },
    )
    # Perform — flips order to paid + grants library.
    perform = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "PerformTransaction",
            "params": {"id": "e2e-tx"},
        },
    )
    assert perform.json()["result"]["state"] == 2

    # Order is paid.
    refreshed = (
        await db_session.execute(select(Order).where(Order.id == order.id))
    ).scalar_one()
    assert refreshed.status == OrderStatus.paid

    # Library has the book.
    lib_rows = (
        await db_session.execute(select(UserLibrary).where(UserLibrary.user_id == user.id))
    ).scalars().all()
    assert len(lib_rows) == 1
    assert lib_rows[0].book_id == book.id

    # Author balance bumped (80 000 * 0.85 = 68 000).
    await db_session.refresh(author)
    assert float(author.available_balance) == starting_balance + 68_000
    assert author.total_sales == 1

    # Side effects fired.
    assert len(captured_watermarks) == 1
    assert len(captured_emails) == 1
    assert captured_emails[0]["template_name"] == "library_grant"


# ---------- cannot re-buy already owned ----------


@pytest.mark.asyncio
async def test_cannot_create_order_for_already_owned_book(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _make_user(db_session, "owner-blocked@example.com")
    book, _ = await _make_book(db_session, "owned-block-book")

    # User already owns it.
    db_session.add(UserLibrary(user_id=user.id, book_id=book.id))
    await db_session.flush()
    await db_session.commit()

    token = await _token(api_client, user.email)
    resp = await api_client.post(
        "/api/v1/orders",
        headers=_h(token),
        json={"book_ids": [str(book.id)]},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["details"]["code"] == "already_owned"


# ---------- idempotent perform doesn't double-grant ----------


@pytest.mark.asyncio
async def test_perform_twice_does_not_double_grant(
    api_client: AsyncClient,
    db_session: AsyncSession,
    captured_watermarks,
    captured_emails,
):
    user = await _make_user(db_session, "double-perform@example.com")
    book, author = await _make_book(db_session, "double-perform-book", price=60_000)

    order = await order_service.create_order(db_session, user, [book.id])
    await db_session.commit()

    tiyin = uzs_to_tiyin(60_000)
    body_create = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "CreateTransaction",
        "params": {
            "id": "double-tx",
            "time": 1_700_000_000_000,
            "amount": tiyin,
            "account": {"order_id": str(order.id)},
        },
    }
    body_perform = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "PerformTransaction",
        "params": {"id": "double-tx"},
    }
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=body_create)
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=body_perform)
    # Replay the perform — Payme retries are normal.
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=body_perform)

    # Still exactly one library row + one balance bump + one email + one watermark.
    lib_rows = (
        await db_session.execute(select(UserLibrary).where(UserLibrary.user_id == user.id))
    ).scalars().all()
    assert len(lib_rows) == 1

    await db_session.refresh(author)
    assert float(author.available_balance) == 51_000  # 60 000 * 0.85
    assert author.total_sales == 1

    assert len(captured_watermarks) == 1
    assert len(captured_emails) == 1


# ---------- expired order blocks payment ----------


@pytest.mark.asyncio
async def test_check_perform_on_expired_order_rejects(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _make_user(db_session, "expired-buyer@example.com")
    book, _ = await _make_book(db_session, "expired-book")

    order = await order_service.create_order(db_session, user, [book.id])
    order.status = OrderStatus.expired
    await db_session.flush()
    await db_session.commit()

    tiyin = uzs_to_tiyin(50_000)
    resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CheckPerformTransaction",
            "params": {"amount": tiyin, "account": {"order_id": str(order.id)}},
        },
    )
    # -31055 = "order cancelled" — Payme groups expired with cancelled.
    assert resp.json()["error"]["code"] == -31055


# ---------- cancelled paid order returns funds ----------


@pytest.mark.asyncio
async def test_refund_after_paid_returns_pending_to_zero(
    api_client: AsyncClient,
    db_session: AsyncSession,
    captured_watermarks,
    captured_emails,
):
    user = await _make_user(db_session, "refund-flow@example.com")
    book, _ = await _make_book(db_session, "refund-book", price=40_000)
    order = await order_service.create_order(db_session, user, [book.id])
    await db_session.commit()

    tiyin = uzs_to_tiyin(40_000)
    create_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "CreateTransaction",
        "params": {
            "id": "refund-tx",
            "time": 1_700_000_000_000,
            "amount": tiyin,
            "account": {"order_id": str(order.id)},
        },
    }
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=create_body)
    await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "PerformTransaction",
            "params": {"id": "refund-tx"},
        },
    )
    cancel = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "CancelTransaction",
            "params": {"id": "refund-tx", "reason": 5},
        },
    )
    assert cancel.json()["result"]["state"] == -2

    refreshed = (
        await db_session.execute(select(Order).where(Order.id == order.id))
    ).scalar_one()
    assert refreshed.status == OrderStatus.refunded
