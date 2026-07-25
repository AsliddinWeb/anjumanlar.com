"""Granular admin scopes.

`User.admin_scopes = None` (the default) keeps the legacy "every admin
sees everything" behaviour. A non-null list restricts a `role=admin`
account to exactly those sections; `superadmin` always bypasses the
check regardless of its own `admin_scopes` value.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security import hash_password
from app.models import User, UserRole
from app.services import user_service

PW = "Hunter22!"


async def _make_user(
    db: AsyncSession,
    email: str,
    role: UserRole = UserRole.reader,
    admin_scopes: list[str] | None = None,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name=email.split("@")[0],
        role=role,
        status="active",
        email_verified=True,
        admin_scopes=admin_scopes,
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


# ---------- service: admin_change_scopes ----------


@pytest.mark.asyncio
async def test_change_scopes_blocks_self_mutation(db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-self@example.com", role=UserRole.admin)
    with pytest.raises(ConflictError):
        await user_service.admin_change_scopes(db_session, admin, admin.id, ["books"])


@pytest.mark.asyncio
async def test_change_scopes_blocks_superadmin_target(db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-vs-super@example.com", role=UserRole.admin)
    super_user = await _make_user(db_session, "scope-super@example.com", role=UserRole.superadmin)
    with pytest.raises(ForbiddenError):
        await user_service.admin_change_scopes(db_session, admin, super_user.id, ["books"])


@pytest.mark.asyncio
async def test_change_scopes_sets_list(db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-setter@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "scope-target@example.com", role=UserRole.admin)
    updated = await user_service.admin_change_scopes(
        db_session, admin, target.id, ["books", "reviews"]
    )
    assert updated.admin_scopes == ["books", "reviews"]


@pytest.mark.asyncio
async def test_change_role_away_from_admin_clears_scopes(db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-demoter@example.com", role=UserRole.admin)
    target = await _make_user(
        db_session, "scope-demote-target@example.com", role=UserRole.admin, admin_scopes=["books"]
    )
    updated = await user_service.admin_change_role(db_session, admin, target.id, UserRole.author)
    assert updated.admin_scopes is None


# ---------- HTTP: require_admin_scope ----------


@pytest.mark.asyncio
async def test_scoped_admin_can_reach_its_scope(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(
        db_session, "scope-books-admin@example.com", role=UserRole.admin, admin_scopes=["books"]
    )
    await db_session.commit()
    token = await _token(api_client, admin.email)

    resp = await api_client.get("/api/v1/books/admin/all", headers=_h(token))
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_scoped_admin_is_403_outside_its_scope(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(
        db_session, "scope-books-only@example.com", role=UserRole.admin, admin_scopes=["books"]
    )
    await db_session.commit()
    token = await _token(api_client, admin.email)

    resp = await api_client.get("/api/v1/admin/withdrawals", headers=_h(token))
    assert resp.status_code == 403
    resp2 = await api_client.get("/api/v1/admin/users", headers=_h(token))
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_unscoped_admin_keeps_full_access(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-unrestricted@example.com", role=UserRole.admin)
    await db_session.commit()
    token = await _token(api_client, admin.email)

    for path in ("/api/v1/books/admin/all", "/api/v1/admin/withdrawals", "/api/v1/admin/users"):
        resp = await api_client.get(path, headers=_h(token))
        assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_superadmin_bypasses_scope_restriction(api_client: AsyncClient, db_session: AsyncSession):
    # Even if a superadmin row somehow carries a restrictive list, the
    # check must still bypass it — scopes only ever apply to `admin`.
    super_user = await _make_user(
        db_session, "scope-super-bypass@example.com", role=UserRole.superadmin, admin_scopes=["books"]
    )
    await db_session.commit()
    token = await _token(api_client, super_user.email)

    resp = await api_client.get("/api/v1/admin/withdrawals", headers=_h(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_scopes_endpoint_updates_target(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-endpoint-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "scope-endpoint-target@example.com", role=UserRole.admin)
    await db_session.commit()
    token = await _token(api_client, admin.email)

    resp = await api_client.patch(
        f"/api/v1/admin/users/{target.id}/scopes",
        headers=_h(token),
        json={"admin_scopes": ["finance", "withdrawals"]},
    )
    assert resp.status_code == 200, resp.text
    assert sorted(resp.json()["admin_scopes"]) == ["finance", "withdrawals"]


@pytest.mark.asyncio
async def test_scopes_endpoint_rejects_unknown_scope(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "scope-bad-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "scope-bad-target@example.com", role=UserRole.admin)
    await db_session.commit()
    token = await _token(api_client, admin.email)

    resp = await api_client.patch(
        f"/api/v1/admin/users/{target.id}/scopes",
        headers=_h(token),
        json={"admin_scopes": ["not-a-real-scope"]},
    )
    assert resp.status_code == 422
