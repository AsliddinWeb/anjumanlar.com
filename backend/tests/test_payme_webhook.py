"""Payme webhook coverage.

We talk to the JSON-RPC endpoint with Basic Auth as Paycom would, then
verify the side-effects on the Order + Payment tables. Each test
focuses on a single state transition so failures point at one method.

The PAYME_SECRET_KEY for tests is monkey-patched to a known value so
the suite doesn't depend on .env shipped with a real key.
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
from app.integrations.payme.client import build_checkout_url, uzs_to_tiyin
from app.models import (
    AuthorProfile,
    Book,
    BookLanguage,
    BookStatus,
    Order,
    OrderStatus,
    Payment,
    PaymentProvider,
    User,
    UserRole,
    UserStatus,
)
from app.services import order_service

PW = "Hunter22!"
TEST_KEY = "test-payme-key-hunter22"
WEBHOOK_PATH = "/api/v1/payments/payme/callback"


@pytest.fixture(autouse=True)
def _payme_key(monkeypatch):
    monkeypatch.setattr(settings, "PAYME_SECRET_KEY", TEST_KEY)
    monkeypatch.setattr(settings, "PAYME_MERCHANT_ID", "test-merchant")
    monkeypatch.setattr(settings, "PAYME_CHECKOUT_URL", "https://checkout.test.paycom.uz")


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


async def _make_book(db: AsyncSession, slug: str, price: float = 50000) -> Book:
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
        user_id=author_user.id, slug=f"prof-{slug}", display_name=f"Prof {slug}"
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
    return book


async def _new_pending_order(db: AsyncSession, slug: str) -> tuple[Order, int]:
    user = await _make_user(db, f"buyer-{slug}@example.com")
    book = await _make_book(db, slug)
    order = await order_service.create_order(db, user, [book.id])
    await db.commit()
    return order, uzs_to_tiyin(float(order.total))


# ---------- auth ----------


@pytest.mark.asyncio
async def test_webhook_rejects_missing_auth(api_client: AsyncClient):
    resp = await api_client.post(
        WEBHOOK_PATH,
        json={"jsonrpc": "2.0", "id": 1, "method": "CheckTransaction", "params": {"id": "x"}},
    )
    body = resp.json()
    assert body["error"]["code"] == -32504


@pytest.mark.asyncio
async def test_webhook_rejects_wrong_password(api_client: AsyncClient):
    resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header("wrong-key"),
        json={"jsonrpc": "2.0", "id": 1, "method": "CheckTransaction", "params": {"id": "x"}},
    )
    assert resp.json()["error"]["code"] == -32504


@pytest.mark.asyncio
async def test_webhook_unknown_method_returns_method_not_found(api_client: AsyncClient):
    resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={"jsonrpc": "2.0", "id": 1, "method": "WhoAmI", "params": {}},
    )
    assert resp.json()["error"]["code"] == -32601


# ---------- CheckPerformTransaction ----------


@pytest.mark.asyncio
async def test_check_perform_allows_pending_order(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "check-ok")
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
    assert resp.json()["result"] == {"allow": True}


@pytest.mark.asyncio
async def test_check_perform_rejects_wrong_amount(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "check-amt")
    resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CheckPerformTransaction",
            "params": {"amount": tiyin + 1, "account": {"order_id": str(order.id)}},
        },
    )
    assert resp.json()["error"]["code"] == -31001


@pytest.mark.asyncio
async def test_check_perform_missing_order(api_client: AsyncClient):
    resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CheckPerformTransaction",
            "params": {"amount": 1000, "account": {"order_id": "no-such-thing"}},
        },
    )
    assert resp.json()["error"]["code"] == -31050


# ---------- CreateTransaction → PerformTransaction happy path ----------


@pytest.mark.asyncio
async def test_create_then_perform_flips_order_to_paid(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "perform-ok")

    create_resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CreateTransaction",
            "params": {
                "id": "tx-perform-ok",
                "time": 1_700_000_000_000,
                "amount": tiyin,
                "account": {"order_id": str(order.id)},
            },
        },
    )
    body = create_resp.json()
    assert "result" in body, body
    assert body["result"]["state"] == 1

    perform_resp = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "PerformTransaction",
            "params": {"id": "tx-perform-ok"},
        },
    )
    perform = perform_resp.json()["result"]
    assert perform["state"] == 2
    assert perform["perform_time"] > 0

    # Order should be paid now.
    refreshed = (
        await db_session.execute(select(Order).where(Order.id == order.id))
    ).scalar_one()
    assert refreshed.status == OrderStatus.paid
    assert refreshed.paid_at is not None


# ---------- Idempotency ----------


@pytest.mark.asyncio
async def test_create_transaction_is_idempotent(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "create-idem")
    params = {
        "id": "tx-idem",
        "time": 1_700_000_000_000,
        "amount": tiyin,
        "account": {"order_id": str(order.id)},
    }
    body = {"jsonrpc": "2.0", "id": 1, "method": "CreateTransaction", "params": params}

    a = (await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=body)).json()
    b = (await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=body)).json()

    assert a["result"]["transaction"] == b["result"]["transaction"]
    assert b["result"]["state"] == 1


@pytest.mark.asyncio
async def test_perform_transaction_is_idempotent(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "perform-idem")
    create_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "CreateTransaction",
        "params": {
            "id": "tx-perform-idem",
            "time": 1_700_000_000_000,
            "amount": tiyin,
            "account": {"order_id": str(order.id)},
        },
    }
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=create_body)

    perform_body = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "PerformTransaction",
        "params": {"id": "tx-perform-idem"},
    }
    a = (await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=perform_body)).json()
    b = (await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=perform_body)).json()

    assert a["result"]["state"] == 2
    assert b["result"]["state"] == 2
    assert a["result"]["perform_time"] == b["result"]["perform_time"]


# ---------- CancelTransaction ----------


@pytest.mark.asyncio
async def test_cancel_pending_transaction_marks_order_cancelled(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "cancel-pending")
    create_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "CreateTransaction",
        "params": {
            "id": "tx-cancel-pending",
            "time": 1_700_000_000_000,
            "amount": tiyin,
            "account": {"order_id": str(order.id)},
        },
    }
    await api_client.post(WEBHOOK_PATH, headers=_auth_header(), json=create_body)

    cancel = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "CancelTransaction",
            "params": {"id": "tx-cancel-pending", "reason": 5},
        },
    )
    assert cancel.json()["result"]["state"] == -1

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.provider_id == "tx-cancel-pending")
        )
    ).scalar_one()
    assert payment.state == -1
    assert payment.reason == 5

    refreshed = (
        await db_session.execute(select(Order).where(Order.id == order.id))
    ).scalar_one()
    assert refreshed.status == OrderStatus.cancelled


@pytest.mark.asyncio
async def test_cancel_after_perform_marks_order_refunded(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "refund")
    tx_id = "tx-refund"
    await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CreateTransaction",
            "params": {
                "id": tx_id,
                "time": 1_700_000_000_000,
                "amount": tiyin,
                "account": {"order_id": str(order.id)},
            },
        },
    )
    await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "PerformTransaction",
            "params": {"id": tx_id},
        },
    )
    cancel = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "CancelTransaction",
            "params": {"id": tx_id, "reason": 3},
        },
    )
    assert cancel.json()["result"]["state"] == -2
    refreshed = (
        await db_session.execute(select(Order).where(Order.id == order.id))
    ).scalar_one()
    assert refreshed.status == OrderStatus.refunded


# ---------- Misc protocol ----------


@pytest.mark.asyncio
async def test_check_transaction_returns_state(
    api_client: AsyncClient, db_session: AsyncSession
):
    order, tiyin = await _new_pending_order(db_session, "check-tx")
    tx_id = "tx-check"
    await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CreateTransaction",
            "params": {
                "id": tx_id,
                "time": 1_700_000_000_000,
                "amount": tiyin,
                "account": {"order_id": str(order.id)},
            },
        },
    )
    check = await api_client.post(
        WEBHOOK_PATH,
        headers=_auth_header(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "CheckTransaction",
            "params": {"id": tx_id},
        },
    )
    result = check.json()["result"]
    assert result["state"] == 1
    assert result["create_time"] == 1_700_000_000_000


# ---------- Checkout URL helper ----------


def test_checkout_url_is_base64_encoded(monkeypatch):
    monkeypatch.setattr(settings, "PAYME_MERCHANT_ID", "TEST123")
    monkeypatch.setattr(settings, "PAYME_CHECKOUT_URL", "https://checkout.test.paycom.uz")
    url = build_checkout_url(
        order_id="order-abc",
        amount_uzs=12345,
        return_url="https://example.com/done",
    )
    assert url.startswith("https://checkout.test.paycom.uz/")
    encoded = url.rsplit("/", 1)[-1]
    decoded = base64.b64decode(encoded).decode()
    assert "m=TEST123" in decoded
    assert "ac.order_id=order-abc" in decoded
    assert "a=1234500" in decoded  # tiyin
