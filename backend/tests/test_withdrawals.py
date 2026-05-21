"""Author balance + withdrawal request coverage.

Walks each transition of the state machine and verifies the balance
arithmetic on AuthorProfile, since that's the data that ends up on the
author's payout statement.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import (
    AuthorProfile,
    User,
    UserRole,
    UserStatus,
    Withdrawal,
    WithdrawalStatus,
)
from app.services import withdrawal_service

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


async def _make_author(
    db: AsyncSession,
    email: str,
    *,
    balance: float = 100_000,
    bank: dict | None = None,
) -> tuple[User, AuthorProfile]:
    user = await _make_user(db, email, role=UserRole.author)
    profile = AuthorProfile(
        user_id=user.id,
        slug=email.split("@")[0],
        display_name=email.split("@")[0],
        available_balance=balance,
        pending_balance=0,
        total_revenue=balance,
        total_sales=1,
        bank_details=bank or {"bank": "Asaka", "account": "1234"},
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return user, profile


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- balance snapshot ----------


@pytest.mark.asyncio
async def test_get_balance_returns_profile_state(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, profile = await _make_author(db_session, "balance-author@example.com", balance=120_000)
    await db_session.commit()
    token = await _token(api_client, user.email)
    resp = await api_client.get("/api/v1/authors/me/balance", headers=_h(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["available_balance"] == 120_000
    assert body["total_sales"] == 1
    assert body["commission_rate"] == 15.0


@pytest.mark.asyncio
async def test_get_balance_404_when_no_author_profile(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _make_user(db_session, "no-profile@example.com")
    await db_session.commit()
    token = await _token(api_client, user.email)
    resp = await api_client.get("/api/v1/authors/me/balance", headers=_h(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["details"]["code"] == "author_profile_missing"


# ---------- request ----------


@pytest.mark.asyncio
async def test_create_request_moves_funds_to_pending(db_session: AsyncSession):
    user, profile = await _make_author(db_session, "req-author@example.com", balance=500_000)

    row = await withdrawal_service.create_request(db_session, user, amount=200_000)
    assert row.status == WithdrawalStatus.requested
    assert float(row.amount) == 200_000

    await db_session.refresh(profile)
    assert float(profile.available_balance) == 300_000
    assert float(profile.pending_balance) == 200_000


@pytest.mark.asyncio
async def test_create_request_rejects_amount_below_minimum(db_session: AsyncSession):
    user, _ = await _make_author(db_session, "small-req@example.com")
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await withdrawal_service.create_request(db_session, user, amount=10_000)


@pytest.mark.asyncio
async def test_create_request_rejects_over_balance(db_session: AsyncSession):
    user, _ = await _make_author(db_session, "over-req@example.com", balance=50_000)
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await withdrawal_service.create_request(db_session, user, amount=100_000)


@pytest.mark.asyncio
async def test_create_request_requires_bank_details(db_session: AsyncSession):
    user, profile = await _make_author(db_session, "nobank@example.com", bank={})
    profile.bank_details = {}
    await db_session.flush()
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await withdrawal_service.create_request(db_session, user, amount=80_000)


# ---------- author cancel ----------


@pytest.mark.asyncio
async def test_author_cancel_returns_funds(db_session: AsyncSession):
    user, profile = await _make_author(db_session, "cancel-author@example.com", balance=400_000)
    row = await withdrawal_service.create_request(db_session, user, amount=150_000)

    await withdrawal_service.cancel_by_author(db_session, user, row.id)
    await db_session.refresh(row)
    await db_session.refresh(profile)
    assert row.status == WithdrawalStatus.cancelled
    assert float(profile.available_balance) == 400_000
    assert float(profile.pending_balance) == 0


# ---------- admin transitions ----------


@pytest.mark.asyncio
async def test_admin_full_completion_flow(db_session: AsyncSession):
    user, profile = await _make_author(db_session, "flow-author@example.com", balance=200_000)
    admin = await _make_user(db_session, "withdraw-admin@example.com", role=UserRole.admin)

    row = await withdrawal_service.create_request(db_session, user, amount=100_000)
    assert float(profile.pending_balance) == 100_000

    await withdrawal_service.admin_approve(db_session, admin, row.id, admin_notes="OK")
    await db_session.refresh(row)
    assert row.status == WithdrawalStatus.approved
    assert row.admin_notes == "OK"

    await withdrawal_service.admin_mark_processing(db_session, admin, row.id)
    await db_session.refresh(row)
    assert row.status == WithdrawalStatus.processing

    await withdrawal_service.admin_mark_completed(
        db_session, admin, row.id, transaction_ref="bank-ref-1"
    )
    await db_session.refresh(row)
    await db_session.refresh(profile)
    assert row.status == WithdrawalStatus.completed
    assert row.transaction_ref == "bank-ref-1"
    # pending bucket clears when funds physically leave the platform.
    assert float(profile.pending_balance) == 0
    assert float(profile.available_balance) == 100_000


@pytest.mark.asyncio
async def test_admin_reject_returns_funds(db_session: AsyncSession):
    user, profile = await _make_author(db_session, "reject-author@example.com", balance=200_000)
    admin = await _make_user(db_session, "reject-admin@example.com", role=UserRole.admin)
    row = await withdrawal_service.create_request(db_session, user, amount=80_000)

    await withdrawal_service.admin_reject(db_session, admin, row.id, admin_notes="bank closed")
    await db_session.refresh(row)
    await db_session.refresh(profile)
    assert row.status == WithdrawalStatus.rejected
    assert row.admin_notes == "bank closed"
    assert float(profile.available_balance) == 200_000
    assert float(profile.pending_balance) == 0


@pytest.mark.asyncio
async def test_non_admin_cannot_approve(db_session: AsyncSession):
    user, _ = await _make_author(db_session, "no-admin@example.com", balance=200_000)
    other = await _make_user(db_session, "no-admin-other@example.com")
    row = await withdrawal_service.create_request(db_session, user, amount=80_000)

    from app.core.exceptions import ForbiddenError

    with pytest.raises(ForbiddenError):
        await withdrawal_service.admin_approve(db_session, other, row.id)


# ---------- HTTP smoke ----------


@pytest.mark.asyncio
async def test_post_request_endpoint_creates_row(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "http-req@example.com", balance=300_000)
    await db_session.commit()
    token = await _token(api_client, user.email)
    resp = await api_client.post(
        "/api/v1/authors/me/withdrawals",
        headers=_h(token),
        json={"amount": 100_000},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "requested"
    assert body["amount"] == 100_000


@pytest.mark.asyncio
async def test_admin_list_visible_to_admin_only(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _make_user(db_session, "reader-list@example.com")
    admin = await _make_user(db_session, "list-admin@example.com", role=UserRole.admin)
    await db_session.commit()

    reader_token = await _token(api_client, user.email)
    admin_token = await _token(api_client, admin.email)

    forbidden = await api_client.get(
        "/api/v1/admin/withdrawals", headers=_h(reader_token)
    )
    assert forbidden.status_code == 403

    ok = await api_client.get("/api/v1/admin/withdrawals", headers=_h(admin_token))
    assert ok.status_code == 200
