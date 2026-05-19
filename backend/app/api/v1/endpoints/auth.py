"""Authentication endpoints — register, verify, login, refresh, logout."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.limiter import limiter
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import AuditAction, User
from app.schemas.auth import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SessionInfo,
    SessionList,
    TokenPair,
    UserPublic,
    UserRegister,
)
from app.services import audit_service, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"


def _client_ip(request: Request) -> str | None:
    """Best-effort client IP. Honours `X-Forwarded-For` first (Nginx in prod
    will set it), falls back to the raw socket peer."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _set_refresh_cookie(response: Response, plain_refresh: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=plain_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _resolve_refresh(body: RefreshRequest | None, cookie_value: str | None) -> str:
    """Refresh token can come from JSON body (native clients) or cookie
    (browser). Body wins so power-users / debuggers can override the cookie."""
    if body and body.refresh_token:
        return body.refresh_token
    if cookie_value:
        return cookie_value
    raise UnauthorizedError("No refresh token supplied")


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new reader account",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    user = await auth_service.register_user(db, data)
    await db.commit()
    await audit_service.log_event(
        AuditAction.register,
        user_id=user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return UserPublic.model_validate(user)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Consume a verification token to activate the account",
)
async def verify_email(
    request: Request,
    data: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    user = await auth_service.verify_email_with_token(db, data.token)
    await db.commit()
    await audit_service.log_event(
        AuditAction.email_verified,
        user_id=user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Email verified")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Reissue a verification email — always returns 200 to avoid leaking emails",
)
@limiter.limit("1/minute")
async def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.resend_verification(db, data.email)
    await db.commit()
    return MessageResponse(
        message="If the email is registered and unverified, a new link has been sent"
    )


# ---------------------------------------------------------------------------
# Login / refresh / logout / me / sessions
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Exchange credentials for an access + refresh token pair",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    ip = _client_ip(request)
    ua = request.headers.get("user-agent")
    try:
        user, access, refresh_plain, _ = await auth_service.login(
            db,
            email=data.email,
            password=data.password,
            user_agent=ua,
            ip_address=ip,
        )
    except (UnauthorizedError, Exception) as exc:
        # Record the failed attempt with the attempted email so admins can
        # spot credential-stuffing campaigns. Then re-raise.
        if isinstance(exc, UnauthorizedError):
            await audit_service.log_event(
                AuditAction.login_failed,
                ip_address=ip,
                user_agent=ua,
                meta={"email": data.email},
            )
        raise
    await db.commit()
    _set_refresh_cookie(response, refresh_plain)
    await audit_service.log_event(
        AuditAction.login_success,
        user_id=user.id,
        ip_address=ip,
        user_agent=ua,
    )
    return LoginResponse(
        access_token=access,
        refresh_token=refresh_plain,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate refresh token — old one becomes immediately invalid",
)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    plain = _resolve_refresh(body, refresh_cookie)
    _, access, new_refresh_plain, _ = await auth_service.refresh_tokens(
        db,
        plain,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    await db.commit()
    _set_refresh_cookie(response, new_refresh_plain)
    return TokenPair(
        access_token=access,
        refresh_token=new_refresh_plain,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the supplied refresh token (this device only)",
)
async def logout(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    plain = (body.refresh_token if body else None) or refresh_cookie
    await auth_service.logout(db, plain)
    await db.commit()
    _clear_refresh_cookie(response)
    await audit_service.log_event(
        AuditAction.logout,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Logged out")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Revoke every refresh token for the current user (sign out all devices)",
)
async def logout_all(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    count = await auth_service.logout_all(db, user.id)
    await db.commit()
    _clear_refresh_cookie(response)
    await audit_service.log_event(
        AuditAction.logout_all,
        user_id=user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        meta={"revoked_count": count},
    )
    return MessageResponse(message=f"Logged out {count} session(s)")


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Return the user profile attached to the current access token",
)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(user)


# ---------------------------------------------------------------------------
# Forgot / reset password
# ---------------------------------------------------------------------------


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Email a password-reset link — always returns 200 to avoid leaking emails",
)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.request_password_reset(db, data.email)
    await db.commit()
    await audit_service.log_event(
        AuditAction.password_reset_requested,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        meta={"email": data.email},
    )
    return MessageResponse(message="If the email is registered, a reset link has been sent")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Consume a reset token and set a new password (kills every active session)",
)
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    user = await auth_service.reset_password_with_token(db, data.token, data.new_password)
    await db.commit()
    _clear_refresh_cookie(response)
    await audit_service.log_event(
        AuditAction.password_reset_completed,
        user_id=user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Password has been reset; please log in again")


@router.get(
    "/sessions",
    response_model=SessionList,
    summary="List active refresh-token sessions for the current user",
)
async def sessions(
    user: Annotated[User, Depends(get_current_user)],
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
) -> SessionList:
    rows = await auth_service.list_active_sessions(db, user.id)

    current_id = None
    if refresh_cookie:
        # Identify "this device" by hashing the cookie and matching against rows.
        from app.core.security import hash_opaque_token

        h = hash_opaque_token(refresh_cookie)
        match = next((r for r in rows if r.token_hash == h), None)
        if match is not None:
            current_id = match.id

    items = [
        SessionInfo(
            id=r.id,
            created_at=r.created_at,
            expires_at=r.expires_at,
            user_agent=r.user_agent,
            # asyncpg returns INET columns as ipaddress objects — coerce to str.
            ip_address=str(r.ip_address) if r.ip_address is not None else None,
            is_current=(current_id is not None and r.id == current_id),
        )
        for r in rows
    ]
    return SessionList(items=items, total=len(items))
