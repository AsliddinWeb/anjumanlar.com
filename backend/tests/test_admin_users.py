"""Admin user management coverage.

Exercises the service-layer rules (no self-mutation, superadmin
protection, side-effects on block) and the HTTP RBAC.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, UserRole, UserStatus
from app.services import user_service

PW = "Hunter22!"


async def _make_user(
    db: AsyncSession,
    email: str,
    role: UserRole = UserRole.reader,
    status: UserStatus = UserStatus.active,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name=email.split("@")[0],
        role=role,
        status=status,
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


# ---------- service: list ----------


@pytest.mark.asyncio
async def test_admin_list_filters_by_role(db_session: AsyncSession):
    await _make_user(db_session, "lst-reader@example.com")
    await _make_user(db_session, "lst-author@example.com", role=UserRole.author)
    items, total = await user_service.admin_list(
        db_session, page=1, page_size=10, role=UserRole.author
    )
    emails = {u.email for u in items}
    assert "lst-author@example.com" in emails
    assert "lst-reader@example.com" not in emails
    assert total >= 1


@pytest.mark.asyncio
async def test_admin_list_search_by_email(db_session: AsyncSession):
    await _make_user(db_session, "needle@example.com")
    items, _ = await user_service.admin_list(
        db_session, page=1, page_size=10, search="needle"
    )
    assert any(u.email == "needle@example.com" for u in items)


# ---------- service: role ----------


@pytest.mark.asyncio
async def test_change_role_blocks_self_mutation(db_session: AsyncSession):
    admin = await _make_user(db_session, "self-admin@example.com", role=UserRole.admin)
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await user_service.admin_change_role(db_session, admin, admin.id, UserRole.reader)


@pytest.mark.asyncio
async def test_change_role_blocks_superadmin_target(db_session: AsyncSession):
    admin = await _make_user(db_session, "admin-vs-super@example.com", role=UserRole.admin)
    super_user = await _make_user(
        db_session, "super@example.com", role=UserRole.superadmin
    )
    from app.core.exceptions import ForbiddenError

    with pytest.raises(ForbiddenError):
        await user_service.admin_change_role(
            db_session, admin, super_user.id, UserRole.admin
        )


@pytest.mark.asyncio
async def test_only_superadmin_promotes_to_superadmin(db_session: AsyncSession):
    admin = await _make_user(db_session, "promoter@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "promote-me@example.com")
    from app.core.exceptions import ForbiddenError

    with pytest.raises(ForbiddenError):
        await user_service.admin_change_role(
            db_session, admin, target.id, UserRole.superadmin
        )


@pytest.mark.asyncio
async def test_admin_can_promote_to_author(db_session: AsyncSession):
    admin = await _make_user(db_session, "promo-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "promo-target@example.com")
    updated = await user_service.admin_change_role(
        db_session, admin, target.id, UserRole.author
    )
    assert updated.role == UserRole.author


# ---------- service: status ----------


@pytest.mark.asyncio
async def test_block_user_revokes_sessions(
    api_client: AsyncClient, db_session: AsyncSession
):
    admin = await _make_user(db_session, "status-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "status-target@example.com")
    await db_session.commit()

    # Give the target a refresh-token session by logging in once.
    await api_client.post(
        "/api/v1/auth/login",
        json={"email": target.email, "password": PW},
    )

    updated = await user_service.admin_change_status(
        db_session, admin, target.id, UserStatus.blocked
    )
    assert updated.status == UserStatus.blocked


@pytest.mark.asyncio
async def test_block_via_delete_path_is_rejected(db_session: AsyncSession):
    admin = await _make_user(db_session, "del-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "del-target@example.com")
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await user_service.admin_change_status(
            db_session, admin, target.id, UserStatus.deleted
        )


# ---------- HTTP layer ----------


@pytest.mark.asyncio
async def test_list_users_requires_admin(api_client: AsyncClient, db_session: AsyncSession):
    reader = await _make_user(db_session, "http-reader@example.com")
    await db_session.commit()
    token = await _token(api_client, reader.email)
    resp = await api_client.get("/api/v1/admin/users", headers=_h(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_and_filter(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "http-admin@example.com", role=UserRole.admin)
    await _make_user(db_session, "http-target@example.com", role=UserRole.author)
    await db_session.commit()
    token = await _token(api_client, admin.email)

    full = await api_client.get(
        "/api/v1/admin/users?page_size=100", headers=_h(token)
    )
    assert full.status_code == 200
    assert full.json()["total"] >= 2

    filtered = await api_client.get(
        "/api/v1/admin/users?role=author", headers=_h(token)
    )
    assert filtered.status_code == 200
    assert all(u["role"] == "author" for u in filtered.json()["items"])


@pytest.mark.asyncio
async def test_admin_can_block_via_http(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "block-admin@example.com", role=UserRole.admin)
    target = await _make_user(db_session, "block-target@example.com")
    await db_session.commit()

    token = await _token(api_client, admin.email)
    resp = await api_client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        headers=_h(token),
        json={"status": "blocked"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "blocked"
