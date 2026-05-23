"""Admin audit log feed — list + filters + RBAC.

The audit writer normally opens its own DB session, so the rollback
fixture can't see those rows. We bypass that by inserting AuditLog
rows directly inside the test session.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import AuditAction, AuditLog, User, UserRole, UserStatus
from app.services import audit_service

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


async def _seed_event(
    db: AsyncSession,
    user: User | None,
    action: AuditAction,
) -> AuditLog:
    row = AuditLog(
        user_id=user.id if user else None,
        action=action,
        ip_address="127.0.0.1",
        meta={},
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


# ---------- service ----------


@pytest.mark.asyncio
async def test_list_audit_orders_newest_first(db_session: AsyncSession):
    user = await _make_user(db_session, "audit-order@example.com")
    await _seed_event(db_session, user, AuditAction.register)
    await _seed_event(db_session, user, AuditAction.login_success)

    items, total = await audit_service.list_audit(db_session, page=1, page_size=10)
    assert total >= 2
    # Most recent first.
    assert items[0].action == AuditAction.login_success


@pytest.mark.asyncio
async def test_list_audit_filters_by_action(db_session: AsyncSession):
    user = await _make_user(db_session, "audit-filter@example.com")
    await _seed_event(db_session, user, AuditAction.login_success)
    await _seed_event(db_session, user, AuditAction.login_failed)

    items, total = await audit_service.list_audit(
        db_session, page=1, page_size=10, action=AuditAction.login_failed
    )
    assert total >= 1
    assert all(r.action == AuditAction.login_failed for r in items)


@pytest.mark.asyncio
async def test_list_audit_filters_by_user(db_session: AsyncSession):
    a = await _make_user(db_session, "audit-a@example.com")
    b = await _make_user(db_session, "audit-b@example.com")
    await _seed_event(db_session, a, AuditAction.login_success)
    await _seed_event(db_session, b, AuditAction.login_success)

    items, total = await audit_service.list_audit(
        db_session, page=1, page_size=10, user_id=a.id
    )
    assert total >= 1
    assert all(r.user_id == a.id for r in items)


# ---------- HTTP ----------


@pytest.mark.asyncio
async def test_audit_requires_admin(api_client: AsyncClient, db_session: AsyncSession):
    reader = await _make_user(db_session, "audit-http-reader@example.com")
    await db_session.commit()
    token = await _token(api_client, reader.email)
    resp = await api_client.get("/api/v1/admin/audit", headers=_h(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_read_audit(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(
        db_session, "audit-http-admin@example.com", role=UserRole.admin
    )
    await _seed_event(db_session, admin, AuditAction.login_success)
    await db_session.commit()
    token = await _token(api_client, admin.email)
    resp = await api_client.get("/api/v1/admin/audit", headers=_h(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert "items" in body
