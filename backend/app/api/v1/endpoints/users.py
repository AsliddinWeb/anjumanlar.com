"""User-centric endpoints: profile read, profile patch, password change,
avatar upload, soft delete.

Role-aware endpoints (admin moderation etc.) land in Phase 5.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import REFRESH_COOKIE_NAME, _clear_refresh_cookie
from app.core.security import hash_opaque_token
from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    MessageResponse,
    UserPublic,
    UserUpdate,
)
from app.services import auth_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Return the logged-in user's profile",
)
async def read_me(user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update mutable profile fields (full_name, preferred_locale, preferences)",
)
async def patch_me(
    data: UserUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    updated = await user_service.update_profile(db, user, data)
    await db.commit()
    return UserPublic.model_validate(updated)


@router.post(
    "/me/password",
    response_model=MessageResponse,
    summary="Change password — current session is kept, other sessions revoked",
)
async def change_password(
    data: ChangePasswordRequest,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    keep_hash = hash_opaque_token(refresh_cookie) if refresh_cookie else None
    revoked = await auth_service.change_password(
        db,
        user,
        current_password=data.current_password,
        new_password=data.new_password,
        keep_token_hash=keep_hash,
    )
    await db.commit()
    if keep_hash is None:
        _clear_refresh_cookie(response)
    return MessageResponse(message=f"Password changed; revoked {revoked} other session(s)")


@router.post(
    "/me/avatar",
    response_model=UserPublic,
    summary="Upload an avatar image (resized to 256x256 JPEG, served from MinIO)",
)
async def upload_avatar(
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    raw = await file.read()
    updated = await user_service.set_avatar(
        db, user, raw, file.content_type or "application/octet-stream"
    )
    await db.commit()
    return UserPublic.model_validate(updated)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete the current account (email freed, every session killed)",
)
async def delete_me(
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Response:
    await user_service.soft_delete(db, user)
    await db.commit()
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# ---------------------------------------------------------------------------
# Smoke endpoint used by Phase 1 tests to exercise the RBAC dependency.
# Real admin endpoints (moderation, user mgmt, …) live in Phase 5.
# ---------------------------------------------------------------------------


@router.get(
    "/admin/ping",
    response_model=MessageResponse,
    summary="Admin-only ping — proves require_admin works end-to-end",
)
async def admin_ping(
    user: Annotated[User, Depends(require_admin)],
) -> MessageResponse:
    return MessageResponse(message=f"hello {user.role.value}")
