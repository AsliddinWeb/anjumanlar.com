"""Password-reset (forgot-password) and in-app change-password flows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models import AuthToken, AuthTokenPurpose, RefreshToken, User, UserStatus
from app.services import auth_service

OLD_PW = "Hunter22!"
NEW_PW = "BrandNew99!"


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    u = User(
        email="pw@example.com",
        password_hash=hash_password(OLD_PW),
        full_name="PW User",
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_delay(**kwargs):
        calls.append(kwargs)

        class _R:
            id = "fake"

        return _R()

    monkeypatch.setattr("app.services.auth_service.send_template_email.delay", fake_delay)
    return calls


# ---------- request_password_reset ----------


@pytest.mark.asyncio
async def test_forgot_password_sends_email_for_known_user(
    db_session: AsyncSession, active_user: User, captured_emails: list[dict[str, Any]]
):
    await auth_service.request_password_reset(db_session, active_user.email)
    assert len(captured_emails) == 1
    assert captured_emails[0]["template_name"] == "password_reset"
    assert "token=" in captured_emails[0]["context"]["reset_url"]


@pytest.mark.asyncio
async def test_forgot_password_silent_for_unknown_email(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    await auth_service.request_password_reset(db_session, "ghost@example.com")
    assert captured_emails == []


@pytest.mark.asyncio
async def test_forgot_password_silent_for_blocked_user(
    db_session: AsyncSession, active_user: User, captured_emails: list[dict[str, Any]]
):
    active_user.status = UserStatus.blocked
    await db_session.flush()
    await auth_service.request_password_reset(db_session, active_user.email)
    assert captured_emails == []


@pytest.mark.asyncio
async def test_forgot_password_invalidates_old_reset_tokens(
    db_session: AsyncSession, active_user: User, captured_emails: list[dict[str, Any]]
):
    await auth_service.request_password_reset(db_session, active_user.email)
    await auth_service.request_password_reset(db_session, active_user.email)

    tokens = (
        (
            await db_session.execute(
                select(AuthToken).where(
                    AuthToken.user_id == active_user.id,
                    AuthToken.purpose == AuthTokenPurpose.password_reset,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(tokens) == 2
    unused = [t for t in tokens if t.used_at is None]
    used = [t for t in tokens if t.used_at is not None]
    assert len(unused) == 1 and len(used) == 1


@pytest.mark.asyncio
async def test_post_forgot_password_always_200(api_client: AsyncClient):
    resp = await api_client.post(
        "/api/v1/auth/forgot-password", json={"email": "noone@example.com"}
    )
    assert resp.status_code == 200


# ---------- reset_password_with_token ----------


@pytest.mark.asyncio
async def test_reset_password_changes_hash_and_kills_sessions(
    db_session: AsyncSession, active_user: User, captured_emails: list[dict[str, Any]]
):
    # Seed two active sessions
    for _ in range(2):
        db_session.add(
            RefreshToken(
                user_id=active_user.id,
                token_hash=hash_opaque_token(generate_opaque_token()),
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
        )
    await db_session.flush()

    await auth_service.request_password_reset(db_session, active_user.email)
    reset_token = captured_emails[0]["context"]["reset_url"].split("token=")[1]
    old_hash = active_user.password_hash

    await auth_service.reset_password_with_token(db_session, reset_token, NEW_PW)
    await db_session.refresh(active_user)

    assert active_user.password_hash != old_hash
    assert verify_password(NEW_PW, active_user.password_hash)
    assert not verify_password(OLD_PW, active_user.password_hash)

    # Every refresh row must be revoked.
    rows = (
        (
            await db_session.execute(
                select(RefreshToken).where(RefreshToken.user_id == active_user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    assert all(r.revoked_at is not None for r in rows)


@pytest.mark.asyncio
async def test_reset_password_rejects_invalid_token(db_session: AsyncSession):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await auth_service.reset_password_with_token(db_session, "bogus", NEW_PW)


@pytest.mark.asyncio
async def test_reset_password_rejects_used_token(
    db_session: AsyncSession, active_user: User, captured_emails: list[dict[str, Any]]
):
    await auth_service.request_password_reset(db_session, active_user.email)
    plain = captured_emails[0]["context"]["reset_url"].split("token=")[1]
    await auth_service.reset_password_with_token(db_session, plain, NEW_PW)

    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await auth_service.reset_password_with_token(db_session, plain, "Another33!")


@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token(db_session: AsyncSession, active_user: User):
    plain = generate_opaque_token()
    db_session.add(
        AuthToken(
            user_id=active_user.id,
            token_hash=hash_opaque_token(plain),
            purpose=AuthTokenPurpose.password_reset,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await db_session.flush()

    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await auth_service.reset_password_with_token(db_session, plain, NEW_PW)


@pytest.mark.asyncio
async def test_post_reset_password_end_to_end(
    api_client: AsyncClient, active_user: User, captured_emails: list[dict[str, Any]]
):
    # Trigger forgot via endpoint to populate captured_emails
    await api_client.post("/api/v1/auth/forgot-password", json={"email": active_user.email})
    token = captured_emails[0]["context"]["reset_url"].split("token=")[1]
    resp = await api_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": NEW_PW},
    )
    assert resp.status_code == 200

    # Login with the new password
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": NEW_PW},
    )
    assert login.status_code == 200


# ---------- change_password ----------


@pytest.mark.asyncio
async def test_change_password_verifies_current_and_swaps_hash(
    db_session: AsyncSession, active_user: User
):
    revoked = await auth_service.change_password(
        db_session, active_user, current_password=OLD_PW, new_password=NEW_PW
    )
    await db_session.refresh(active_user)
    assert verify_password(NEW_PW, active_user.password_hash)
    assert revoked == 0  # no sessions seeded


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current(db_session: AsyncSession, active_user: User):
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        await auth_service.change_password(
            db_session,
            active_user,
            current_password="WrongOld1!",
            new_password=NEW_PW,
        )


@pytest.mark.asyncio
async def test_change_password_keeps_caller_session_revokes_others(
    db_session: AsyncSession, active_user: User
):
    keep_plain = generate_opaque_token()
    keep_hash = hash_opaque_token(keep_plain)
    other_plain = generate_opaque_token()

    db_session.add_all(
        [
            RefreshToken(
                user_id=active_user.id,
                token_hash=keep_hash,
                expires_at=datetime.now(UTC) + timedelta(days=7),
            ),
            RefreshToken(
                user_id=active_user.id,
                token_hash=hash_opaque_token(other_plain),
                expires_at=datetime.now(UTC) + timedelta(days=7),
            ),
        ]
    )
    await db_session.flush()

    revoked = await auth_service.change_password(
        db_session,
        active_user,
        current_password=OLD_PW,
        new_password=NEW_PW,
        keep_token_hash=keep_hash,
    )
    assert revoked == 1

    rows = (
        (
            await db_session.execute(
                select(RefreshToken).where(RefreshToken.user_id == active_user.id)
            )
        )
        .scalars()
        .all()
    )
    keep_row = next(r for r in rows if r.token_hash == keep_hash)
    other_row = next(r for r in rows if r.token_hash != keep_hash)
    assert keep_row.revoked_at is None
    assert other_row.revoked_at is not None


@pytest.mark.asyncio
async def test_post_users_me_password_requires_bearer(api_client: AsyncClient):
    resp = await api_client.post(
        "/api/v1/users/me/password",
        json={"current_password": OLD_PW, "new_password": NEW_PW},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_users_me_password_end_to_end(api_client: AsyncClient, active_user: User):
    login = (
        await api_client.post(
            "/api/v1/auth/login",
            json={"email": active_user.email, "password": OLD_PW},
        )
    ).json()
    resp = await api_client.post(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"current_password": OLD_PW, "new_password": NEW_PW},
    )
    assert resp.status_code == 200
    # Login with new password works
    new_login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": NEW_PW},
    )
    assert new_login.status_code == 200
