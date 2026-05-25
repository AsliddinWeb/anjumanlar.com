"""Business logic for the /auth/* endpoints.

Service functions:

- never commit — the endpoint owns the transaction boundary.
- raise app-level exceptions from `app.core.exceptions`; the global handler
  maps them to JSON responses.
- enqueue Celery tasks for side-effects (email). They are fire-and-forget;
  if the worker is down the registration still succeeds and the task waits
  in the broker.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models import AuthToken, AuthTokenPurpose, RefreshToken, User, UserStatus
from app.schemas.auth import UserRegister
from app.tasks.email_tasks import send_template_email


def _build_verify_url(token: str, locale: str) -> str:
    return f"{settings.FRONTEND_URL}/{locale}/auth/verify-email?token={token}"


async def _issue_verification_token(db: AsyncSession, user: User) -> str:
    """Mint a new verify-email token row, returning the plaintext to email."""
    plain = generate_opaque_token()
    db.add(
        AuthToken(
            user_id=user.id,
            token_hash=hash_opaque_token(plain),
            purpose=AuthTokenPurpose.email_verification,
            expires_at=datetime.now(UTC) + timedelta(hours=settings.EMAIL_VERIFY_TOKEN_TTL_HOURS),
        )
    )
    await db.flush()
    return plain


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Create a new ``reader`` account in ``pending`` status, fire welcome +
    verify emails. Raises :class:`ConflictError` if the email is taken."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email already registered", details={"code": "email_taken"})

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        preferred_locale=data.preferred_locale,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    plain_token = await _issue_verification_token(db, user)
    verify_url = _build_verify_url(plain_token, user.preferred_locale)

    # Fire-and-forget side-effects. Each .delay() lands a job on Redis.
    send_template_email.delay(
        to=user.email,
        template_name="welcome",
        locale=user.preferred_locale,
        context={"full_name": user.full_name, "email": user.email},
    )
    send_template_email.delay(
        to=user.email,
        template_name="verify_email",
        locale=user.preferred_locale,
        context={
            "full_name": user.full_name,
            "verify_url": verify_url,
            "expires_in_hours": settings.EMAIL_VERIFY_TOKEN_TTL_HOURS,
        },
    )
    return user


async def verify_email_with_token(db: AsyncSession, plain_token: str) -> User:
    """Consume a verification token, activate the user. Each token fires once."""
    token_hash = hash_opaque_token(plain_token)
    row = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.purpose == AuthTokenPurpose.email_verification,
        )
    )
    token = row.scalar_one_or_none()
    if token is None:
        raise NotFoundError("Invalid verification token", details={"code": "invalid_token"})
    if token.used_at is not None:
        raise ConflictError("Token already used", details={"code": "token_used"})
    if token.expires_at < datetime.now(UTC):
        raise ValidationError("Token expired", details={"code": "token_expired"})

    token.used_at = datetime.now(UTC)

    user = (await db.execute(select(User).where(User.id == token.user_id))).scalar_one()
    user.email_verified = True
    if user.status == UserStatus.pending:
        user.status = UserStatus.active

    await db.flush()
    await db.refresh(user)
    return user


async def resend_verification(db: AsyncSession, email: str) -> None:
    """Issue a fresh verification token + email, silently no-op if the user
    doesn't exist or is already verified. The endpoint always returns 200 so
    we don't leak which emails are registered."""
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or user.email_verified:
        return

    # Invalidate prior unused verification tokens so the old links stop working.
    await db.execute(
        update(AuthToken)
        .where(
            AuthToken.user_id == user.id,
            AuthToken.purpose == AuthTokenPurpose.email_verification,
            AuthToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )

    plain_token = await _issue_verification_token(db, user)
    verify_url = _build_verify_url(plain_token, user.preferred_locale)
    send_template_email.delay(
        to=user.email,
        template_name="verify_email",
        locale=user.preferred_locale,
        context={
            "full_name": user.full_name,
            "verify_url": verify_url,
            "expires_in_hours": settings.EMAIL_VERIFY_TOKEN_TTL_HOURS,
        },
    )


# ---------------------------------------------------------------------------
# Login + refresh-token rotation
# ---------------------------------------------------------------------------


async def _issue_token_pair(
    db: AsyncSession,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str, RefreshToken]:
    """Mint a fresh (access_jwt, refresh_plaintext, refresh_row) triple."""
    access = create_access_token(str(user.id))

    refresh_plain = generate_opaque_token()
    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_opaque_token(refresh_plain),
        expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(refresh_row)
    await db.flush()
    await db.refresh(refresh_row)
    return access, refresh_plain, refresh_row


async def login(
    db: AsyncSession,
    email: str,
    password: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, str, str, RefreshToken]:
    """Verify credentials, mint a token pair, stamp ``last_login_at``.

    A "user not found" and a "wrong password" both surface as the same
    :class:`UnauthorizedError` so attackers can't enumerate accounts.
    """
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid email or password", details={"code": "invalid_credentials"})
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password", details={"code": "invalid_credentials"})
    if user.status == UserStatus.blocked:
        raise ForbiddenError("Account blocked", details={"code": "account_blocked"})

    access, refresh_plain, refresh_row = await _issue_token_pair(
        db, user, user_agent=user_agent, ip_address=ip_address
    )

    user.last_login_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(user)

    return user, access, refresh_plain, refresh_row


async def _lookup_active_refresh(db: AsyncSession, plain_token: str) -> RefreshToken:
    row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(plain_token))
        )
    ).scalar_one_or_none()
    if row is None:
        raise UnauthorizedError("Invalid refresh token")
    if row.revoked_at is not None:
        raise UnauthorizedError("Refresh token revoked")
    if row.expires_at < datetime.now(UTC):
        raise UnauthorizedError("Refresh token expired")
    return row


async def refresh_tokens(
    db: AsyncSession,
    plain_refresh: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, str, str, RefreshToken]:
    """Rotate: revoke the supplied refresh, issue a fresh pair."""
    old = await _lookup_active_refresh(db, plain_refresh)

    user = (await db.execute(select(User).where(User.id == old.user_id))).scalar_one_or_none()
    if user is None or user.status == UserStatus.blocked:
        raise UnauthorizedError("Account unavailable")

    old.revoked_at = datetime.now(UTC)

    access, refresh_plain, refresh_row = await _issue_token_pair(
        db, user, user_agent=user_agent, ip_address=ip_address
    )
    await db.flush()
    return user, access, refresh_plain, refresh_row


async def logout(db: AsyncSession, plain_refresh: str | None) -> None:
    """Revoke a single refresh token. Silent on unknown/missing tokens so
    repeated logouts don't error."""
    if not plain_refresh:
        return
    row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(plain_refresh))
        )
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        return
    row.revoked_at = datetime.now(UTC)
    await db.flush()


async def logout_all(db: AsyncSession, user_id: UUID) -> int:
    """Revoke every active refresh token for the user. Returns the count
    that got revoked — useful for confirming devices-signed-out in the UI."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await db.flush()
    return result.rowcount or 0


async def list_active_sessions(db: AsyncSession, user_id: UUID) -> list[RefreshToken]:
    """All non-revoked, non-expired refresh rows belonging to ``user_id``,
    newest first."""
    now = datetime.now(UTC)
    rows = (
        (
            await db.execute(
                select(RefreshToken)
                .where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                    RefreshToken.expires_at > now,
                )
                .order_by(RefreshToken.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


# ---------------------------------------------------------------------------
# Password reset (forgot-password flow) + change (logged-in flow)
# ---------------------------------------------------------------------------


def _build_reset_url(token: str, locale: str) -> str:
    return f"{settings.FRONTEND_URL}/{locale}/auth/reset-password?token={token}"


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Email-bound reset flow. Silent on unknown / blocked accounts
    so attackers can't enumerate emails. Any previously-issued unused reset
    tokens are invalidated so old links stop working."""
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or user.status == UserStatus.blocked:
        return

    await db.execute(
        update(AuthToken)
        .where(
            AuthToken.user_id == user.id,
            AuthToken.purpose == AuthTokenPurpose.password_reset,
            AuthToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )

    plain = generate_opaque_token()
    db.add(
        AuthToken(
            user_id=user.id,
            token_hash=hash_opaque_token(plain),
            purpose=AuthTokenPurpose.password_reset,
            expires_at=datetime.now(UTC) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_TTL_HOURS),
        )
    )
    await db.flush()

    send_template_email.delay(
        to=user.email,
        template_name="password_reset",
        locale=user.preferred_locale,
        context={
            "full_name": user.full_name,
            "reset_url": _build_reset_url(plain, user.preferred_locale),
            "expires_in_hours": settings.PASSWORD_RESET_TOKEN_TTL_HOURS,
        },
    )


async def reset_password_with_token(db: AsyncSession, plain_token: str, new_password: str) -> User:
    """Consume a reset token, set the new password, kill every active
    session. The user must log in again everywhere."""
    token_hash = hash_opaque_token(plain_token)
    token = (
        await db.execute(
            select(AuthToken).where(
                AuthToken.token_hash == token_hash,
                AuthToken.purpose == AuthTokenPurpose.password_reset,
            )
        )
    ).scalar_one_or_none()
    if token is None:
        raise NotFoundError("Invalid reset token", details={"code": "invalid_token"})
    if token.used_at is not None:
        raise ConflictError("Token already used", details={"code": "token_used"})
    if token.expires_at < datetime.now(UTC):
        raise ValidationError("Token expired", details={"code": "token_expired"})

    user = (await db.execute(select(User).where(User.id == token.user_id))).scalar_one()
    if user.status == UserStatus.blocked:
        raise UnauthorizedError("Account unavailable")

    token.used_at = datetime.now(UTC)
    user.password_hash = hash_password(new_password)

    # Reset implies "someone else might have access" — revoke every session.
    await logout_all(db, user.id)
    await db.flush()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
    *,
    keep_token_hash: str | None = None,
) -> int:
    """Verify the current password, set the new one, revoke every refresh
    token except the one whose ``token_hash`` matches ``keep_token_hash``
    (typically the caller's own session). Returns the number of revoked
    sessions for UI feedback."""
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")

    user.password_hash = hash_password(new_password)

    now = datetime.now(UTC)
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    if keep_token_hash is not None:
        stmt = stmt.where(RefreshToken.token_hash != keep_token_hash)
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0
