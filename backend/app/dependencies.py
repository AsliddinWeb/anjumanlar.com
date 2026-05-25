"""FastAPI dependencies that all `/api/v1/*` routers share.

The Bearer scheme is registered with a `tokenUrl` so the Swagger "Authorize"
button knows where logins happen. We set `auto_error=False` so missing /
malformed headers raise *our* :class:`UnauthorizedError` instead of FastAPI's
default detail-only response — that keeps every error in the API a uniform
``{"error": {"code": ..., "message": ...}}`` shape.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User, UserRole, UserStatus

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise UnauthorizedError("Missing access token")

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired access token")

    raw_sub = payload.get("sub")
    if not raw_sub:
        raise UnauthorizedError("Malformed access token")
    try:
        user_id = UUID(raw_sub)
    except ValueError as exc:
        raise UnauthorizedError("Malformed access token") from exc

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if user.status == UserStatus.blocked:
        raise ForbiddenError("Account blocked")
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.status != UserStatus.active:
        raise ForbiddenError("Account is not active")
    return user


async def get_current_verified_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.email_verified:
        raise ForbiddenError("Email not verified")
    return user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


def require_roles(*allowed: UserRole):
    """Factory: returns a FastAPI dependency that 403s if the caller's role
    is not in ``allowed``. Pre-built aliases below cover the common cases."""
    allowed_set = set(allowed)

    async def _checker(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in allowed_set:
            raise ForbiddenError(
                f"Insufficient privileges (required: {sorted(r.value for r in allowed_set)})"
            )
        return user

    return _checker


# `author` is the lowest tier that can upload books; admin + superadmin
# inherit the right. `admin` covers moderation; `superadmin` is reserved for
# tenant-level config.
require_author = require_roles(UserRole.author, UserRole.admin, UserRole.superadmin)
require_admin = require_roles(UserRole.admin, UserRole.superadmin)
require_superadmin = require_roles(UserRole.superadmin)
