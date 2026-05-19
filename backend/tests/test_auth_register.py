"""Register + email-verification flow.

Service-level tests use the ``db_session`` rollback fixture and call
``app.services.auth_service`` directly. Endpoint-level tests go through the
ASGI client with a dependency override so they share the same rolled-back
session — keeps the real DB clean between runs.

Celery's ``send_template_email.delay`` is monkeypatched to record calls
without actually enqueueing — we don't need MailHog for these.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_opaque_token, hash_opaque_token
from app.models import AuthToken, AuthTokenPurpose, User, UserStatus
from app.schemas.auth import UserRegister
from app.services import auth_service

VALID_PW = "Hunter22!"  # passes the 8+/upper/lower/digit policy


# ---------- fixtures ----------


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace `send_template_email.delay` with a recorder."""
    calls: list[dict[str, Any]] = []

    def fake_delay(**kwargs):
        calls.append(kwargs)

        class _Result:
            id = "fake-task-id"

        return _Result()

    monkeypatch.setattr("app.services.auth_service.send_template_email.delay", fake_delay)
    return calls


# ---------- service-layer ----------


@pytest.mark.asyncio
async def test_register_creates_pending_user(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    user = await auth_service.register_user(
        db_session,
        UserRegister(
            email="alice@example.com",
            password=VALID_PW,
            full_name="Alice",
            preferred_locale="uz",
        ),
    )
    assert user.id is not None
    assert user.status == UserStatus.pending
    assert user.email_verified is False
    assert user.password_hash != VALID_PW

    # Exactly one verification token row exists for this user.
    tokens = (
        (
            await db_session.execute(
                select(AuthToken).where(
                    AuthToken.user_id == user.id,
                    AuthToken.purpose == AuthTokenPurpose.email_verification,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(tokens) == 1

    # Two emails enqueued: welcome + verify.
    assert [c["template_name"] for c in captured_emails] == ["welcome", "verify_email"]
    assert captured_emails[1]["context"]["verify_url"].startswith("http")


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    base = UserRegister(
        email="dup@example.com", password=VALID_PW, full_name="Dup", preferred_locale="uz"
    )
    await auth_service.register_user(db_session, base)

    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await auth_service.register_user(db_session, base)


@pytest.mark.asyncio
async def test_verify_email_activates_user(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    user = await auth_service.register_user(
        db_session,
        UserRegister(
            email="verify@example.com",
            password=VALID_PW,
            full_name="Vivi",
            preferred_locale="uz",
        ),
    )
    plain = captured_emails[1]["context"]["verify_url"].split("token=")[1]

    activated = await auth_service.verify_email_with_token(db_session, plain)
    assert activated.id == user.id
    assert activated.email_verified is True
    assert activated.status == UserStatus.active


@pytest.mark.asyncio
async def test_verify_email_rejects_invalid_token(db_session: AsyncSession):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await auth_service.verify_email_with_token(db_session, "totally-bogus")


@pytest.mark.asyncio
async def test_verify_email_rejects_used_token(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    await auth_service.register_user(
        db_session,
        UserRegister(
            email="used@example.com", password=VALID_PW, full_name="U", preferred_locale="uz"
        ),
    )
    plain = captured_emails[1]["context"]["verify_url"].split("token=")[1]
    await auth_service.verify_email_with_token(db_session, plain)

    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await auth_service.verify_email_with_token(db_session, plain)


@pytest.mark.asyncio
async def test_verify_email_rejects_expired_token(db_session: AsyncSession):
    """Manually create a user + expired token to bypass the issue path."""
    user = User(
        email="expired@example.com",
        password_hash="$2b$12$abcdefghijklmnopqrstuv",
        full_name="Exp",
    )
    db_session.add(user)
    await db_session.flush()

    plain = generate_opaque_token()
    db_session.add(
        AuthToken(
            user_id=user.id,
            token_hash=hash_opaque_token(plain),
            purpose=AuthTokenPurpose.email_verification,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await db_session.flush()

    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await auth_service.verify_email_with_token(db_session, plain)


@pytest.mark.asyncio
async def test_resend_verification_silent_for_unknown_email(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    await auth_service.resend_verification(db_session, "nobody@example.com")
    assert captured_emails == []  # nothing sent, no error


@pytest.mark.asyncio
async def test_resend_verification_silent_for_already_verified(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    user = await auth_service.register_user(
        db_session,
        UserRegister(
            email="done@example.com", password=VALID_PW, full_name="Done", preferred_locale="uz"
        ),
    )
    user.email_verified = True
    await db_session.flush()

    before = len(captured_emails)
    await auth_service.resend_verification(db_session, user.email)
    # captured_emails still has the original 2 from register; no new entry.
    assert len(captured_emails) == before


@pytest.mark.asyncio
async def test_resend_verification_revokes_old_tokens_and_sends_new(
    db_session: AsyncSession, captured_emails: list[dict[str, Any]]
):
    user = await auth_service.register_user(
        db_session,
        UserRegister(
            email="re@example.com", password=VALID_PW, full_name="Re", preferred_locale="uz"
        ),
    )
    captured_emails.clear()  # forget the register-time emails

    await auth_service.resend_verification(db_session, "re@example.com")

    # Scope by user_id — other committed users in the dev DB shouldn't bleed in.
    tokens = (
        (
            await db_session.execute(
                select(AuthToken).where(
                    AuthToken.user_id == user.id,
                    AuthToken.purpose == AuthTokenPurpose.email_verification,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(tokens) == 2  # one used-at marked, one fresh
    fresh = [t for t in tokens if t.used_at is None]
    used = [t for t in tokens if t.used_at is not None]
    assert len(fresh) == 1 and len(used) == 1

    assert len(captured_emails) == 1
    assert captured_emails[0]["template_name"] == "verify_email"


# ---------- endpoint-layer ----------


@pytest.mark.asyncio
async def test_post_register_returns_201_and_user_payload(
    api_client: AsyncClient, captured_emails: list[dict[str, Any]]
):
    resp = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e@example.com",
            "password": VALID_PW,
            "full_name": "E2E",
            "preferred_locale": "uz",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "e2e@example.com"
    assert body["status"] == "pending"
    assert body["email_verified"] is False
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_post_register_rejects_weak_password(api_client: AsyncClient):
    resp = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "W",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_register_rejects_duplicate(
    api_client: AsyncClient, captured_emails: list[dict[str, Any]]
):
    payload = {
        "email": "twice@example.com",
        "password": VALID_PW,
        "full_name": "T",
    }
    await api_client.post("/api/v1/auth/register", json=payload)
    resp = await api_client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_post_verify_email_end_to_end(
    api_client: AsyncClient, captured_emails: list[dict[str, Any]]
):
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": "v-e2e@example.com", "password": VALID_PW, "full_name": "V"},
    )
    plain = captured_emails[1]["context"]["verify_url"].split("token=")[1]
    resp = await api_client.post("/api/v1/auth/verify-email", json={"token": plain})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified"


@pytest.mark.asyncio
async def test_post_resend_verification_always_200(api_client: AsyncClient):
    """No leak: unknown email must still return 200."""
    resp = await api_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "ghost@example.com"},
    )
    assert resp.status_code == 200
