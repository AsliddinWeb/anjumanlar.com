"""Rate limiting + audit log + security headers tests.

The rate-limit test re-enables the limiter and flushes Redis db 0 before /
after so it doesn't pollute neighbouring tests. Everything else runs with
the limiter disabled (see conftest)."""

from __future__ import annotations

import pytest
import redis.asyncio as redis_async
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.limiter import limiter
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import AuditAction, AuditLog, User, UserStatus

PW = "Hunter22!"


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    u = User(
        email="audit@example.com",
        password_hash=hash_password(PW),
        full_name="Audit User",
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


# ---------- Security headers ----------


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "same-origin"
    assert "permissions-policy" in resp.headers


@pytest.mark.asyncio
async def test_hsts_only_in_production(client: AsyncClient):
    # ENVIRONMENT defaults to development; HSTS must NOT appear here.
    resp = await client.get("/health")
    assert "strict-transport-security" not in resp.headers


# ---------- Audit log ----------


async def _query_audits(action: AuditAction) -> list[AuditLog]:
    """Audits live in their own transaction so we read them in a fresh
    session, NOT the rollback fixture's."""
    async with AsyncSessionLocal() as s:
        rows = (await s.execute(select(AuditLog).where(AuditLog.action == action))).scalars().all()
        return list(rows)


async def _purge_audits(action: AuditAction) -> None:
    """Clean up audit rows written by an earlier test so counts stay scoped."""
    async with AsyncSessionLocal() as s:
        from sqlalchemy import delete

        await s.execute(delete(AuditLog).where(AuditLog.action == action))
        await s.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success_writes_audit():
    """The audit service uses its own session, so it can't see users created
    inside the rollback fixture. Bypass api_client and the test session here:
    commit a real user, hit the live backend over localhost:8000, then clean
    up both the audit row and the user."""
    import httpx as _httpx
    from sqlalchemy import delete

    email = "audit-success-e2e@example.com"
    async with AsyncSessionLocal() as s:
        u = User(
            email=email,
            password_hash=hash_password(PW),
            full_name="Audit E2E",
            status=UserStatus.active,
            email_verified=True,
        )
        s.add(u)
        await s.commit()
        await s.refresh(u)
        user_id = u.id

    try:
        async with _httpx.AsyncClient(base_url="http://localhost:8000", timeout=5) as c:
            resp = await c.post(
                "/api/v1/auth/login",
                json={"email": email, "password": PW},
            )
        assert resp.status_code == 200, resp.text
        rows = await _query_audits(AuditAction.login_success)
        assert any(r.user_id == user_id for r in rows)
    finally:
        async with AsyncSessionLocal() as s:
            await s.execute(delete(AuditLog).where(AuditLog.user_id == user_id))
            await s.execute(delete(User).where(User.id == user_id))
            await s.commit()


@pytest.mark.audit_enabled
@pytest.mark.asyncio
async def test_login_failed_writes_audit_with_null_user_id(
    api_client: AsyncClient, active_user: User
):
    await _purge_audits(AuditAction.login_failed)
    await api_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "WrongPass1!"},
    )
    rows = await _query_audits(AuditAction.login_failed)
    assert len(rows) == 1
    assert rows[0].user_id is None  # service raised before identifying the user
    assert rows[0].meta.get("email") == active_user.email
    await _purge_audits(AuditAction.login_failed)


# ---------- Rate limiting ----------


@pytest.fixture
async def with_limiter_enabled():
    """Re-enable the limiter + flush Redis db 0 (slowapi's storage)."""
    r = redis_async.from_url(settings.REDIS_URL)
    await r.flushdb()
    limiter.enabled = True
    try:
        yield
    finally:
        limiter.enabled = False
        await r.flushdb()
        await r.aclose()


@pytest.mark.asyncio
async def test_login_returns_429_after_limit(api_client: AsyncClient, with_limiter_enabled):
    """11th login attempt within the window must hit /minute limit (10)."""
    last_status = None
    statuses = []
    for _ in range(12):
        resp = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "x@example.com", "password": "wrong"},
        )
        statuses.append(resp.status_code)
        last_status = resp.status_code
    assert 429 in statuses, f"got statuses: {statuses}"
    # Final response payload uses our error envelope.
    if last_status == 429:
        body = resp.json()
        assert body["error"]["code"] == "rate_limited"


@pytest.mark.asyncio
async def test_forgot_password_rate_limited_at_3_per_minute(
    api_client: AsyncClient, with_limiter_enabled
):
    statuses = []
    for _ in range(5):
        resp = await api_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "x@example.com"},
        )
        statuses.append(resp.status_code)
    # 1..3 → 200; 4..5 → 429
    assert statuses.count(200) == 3
    assert statuses.count(429) == 2
