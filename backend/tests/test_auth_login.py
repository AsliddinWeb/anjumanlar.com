"""Login, token rotation, logout, /me, /sessions.

These tests don't enqueue emails so they don't need the ``captured_emails``
fixture; they do need ``api_client`` (HTTP) and ``db_session`` (DB), both
from conftest.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import RefreshToken, User, UserStatus

VALID_PW = "Hunter22!"


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    """A verified, active reader with a known password."""
    u = User(
        email="active@example.com",
        password_hash=hash_password(VALID_PW),
        full_name="Active User",
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _login(api_client: AsyncClient, email: str, password: str):
    return await api_client.post("/api/v1/auth/login", json={"email": email, "password": password})


# ---------- login ----------


@pytest.mark.asyncio
async def test_login_success_returns_pair_and_sets_cookie(
    api_client: AsyncClient, active_user: User
):
    resp = await _login(api_client, active_user.email, VALID_PW)
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 30 * 60
    assert body["user"]["email"] == active_user.email
    assert body["user"]["status"] == "active"

    # httpOnly refresh cookie set on the response.
    assert "refresh_token" in resp.cookies
    cookie = resp.cookies["refresh_token"]
    assert cookie == body["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_is_401_with_generic_message(
    api_client: AsyncClient, active_user: User
):
    resp = await _login(api_client, active_user.email, "WrongPass1!")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_login_unknown_email_is_401(api_client: AsyncClient):
    """Must not leak whether the email is registered — same 401 as wrong-pw."""
    resp = await _login(api_client, "ghost@example.com", VALID_PW)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_blocked_user_is_403(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    active_user.status = UserStatus.blocked
    await db_session.flush()
    resp = await _login(api_client, active_user.email, VALID_PW)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_records_refresh_row_with_ua_and_ip(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    await _login(api_client, active_user.email, VALID_PW)
    row = (
        await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == active_user.id))
    ).scalar_one()
    assert row.user_agent is not None  # AsyncClient sets one
    assert row.revoked_at is None
    assert row.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_login_updates_last_login_at(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    assert active_user.last_login_at is None
    await _login(api_client, active_user.email, VALID_PW)
    await db_session.refresh(active_user)
    assert active_user.last_login_at is not None


# ---------- refresh rotation ----------


@pytest.mark.asyncio
async def test_refresh_rotates_and_invalidates_old_token(
    api_client: AsyncClient, active_user: User
):
    first = (await _login(api_client, active_user.email, VALID_PW)).json()
    old_refresh = first["refresh_token"]

    rot = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rot.status_code == 200
    new = rot.json()
    assert new["refresh_token"] != old_refresh

    # Reusing the rotated-out token must fail.
    replay = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_is_401(api_client: AsyncClient):
    resp = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_expired_token_is_401(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    first = (await _login(api_client, active_user.email, VALID_PW)).json()
    # Mark the underlying refresh row as already expired.
    row = (
        await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == active_user.id))
    ).scalar_one()
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.flush()

    resp = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert resp.status_code == 401


# ---------- logout ----------


@pytest.mark.asyncio
async def test_logout_revokes_only_one_session(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    a = (await _login(api_client, active_user.email, VALID_PW)).json()
    b = (await _login(api_client, active_user.email, VALID_PW)).json()

    resp = await api_client.post("/api/v1/auth/logout", json={"refresh_token": a["refresh_token"]})
    assert resp.status_code == 200

    # Session A's refresh is dead; session B still works.
    a_replay = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": a["refresh_token"]}
    )
    assert a_replay.status_code == 401

    b_replay = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": b["refresh_token"]}
    )
    assert b_replay.status_code == 200


@pytest.mark.asyncio
async def test_logout_all_kills_every_session(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    a = (await _login(api_client, active_user.email, VALID_PW)).json()
    b = (await _login(api_client, active_user.email, VALID_PW)).json()

    headers = {"Authorization": f"Bearer {a['access_token']}"}
    resp = await api_client.post("/api/v1/auth/logout-all", headers=headers)
    assert resp.status_code == 200
    assert "2 session(s)" in resp.json()["message"]

    for tok in (a["refresh_token"], b["refresh_token"]):
        replay = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": tok})
        assert replay.status_code == 401


# ---------- /me ----------


@pytest.mark.asyncio
async def test_me_requires_bearer(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_garbage_token(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(api_client: AsyncClient, active_user: User):
    login_body = (await _login(api_client, active_user.email, VALID_PW)).json()
    resp = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == active_user.email


@pytest.mark.asyncio
async def test_me_blocks_when_user_status_becomes_blocked(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    login_body = (await _login(api_client, active_user.email, VALID_PW)).json()
    active_user.status = UserStatus.blocked
    await db_session.flush()

    resp = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )
    assert resp.status_code == 403


# ---------- /sessions ----------


@pytest.mark.asyncio
async def test_sessions_lists_only_active_rows(
    api_client: AsyncClient, db_session: AsyncSession, active_user: User
):
    # Login twice — two active sessions
    a = (await _login(api_client, active_user.email, VALID_PW)).json()
    b = (await _login(api_client, active_user.email, VALID_PW)).json()
    # Logout B — A remains
    await api_client.post("/api/v1/auth/logout", json={"refresh_token": b["refresh_token"]})

    resp = await api_client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {a['access_token']}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["user_agent"] is not None
