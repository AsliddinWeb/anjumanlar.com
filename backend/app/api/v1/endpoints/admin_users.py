"""Admin-only user management endpoints.

Lives under ``/admin/users/*``. Read + role + status mutations; deletion
still flows through the per-user ``DELETE /users/me`` endpoint by design
(an admin who really wants a user gone can demote → block them, or
ssh in for the soft-delete corner case).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import User, UserRole, UserStatus
from app.schemas.auth import (
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    UserList,
    UserPublic,
)
from app.services import user_service

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get(
    "",
    response_model=UserList,
    summary="List users with optional search + role/status filters (admin+)",
)
async def admin_list_users(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=200),
    role: UserRole | None = None,
    status_filter: UserStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> UserList:
    items, total = await user_service.admin_list(
        db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        status=status_filter,
    )
    return UserList(
        items=[UserPublic.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserPublic,
    summary="Change a user's role (admin+; superadmin promotions are superadmin-only)",
)
async def admin_change_user_role(
    user_id: UUID,
    data: AdminUserRoleUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    target = await user_service.admin_change_role(db, admin, user_id, data.role)
    await db.commit()
    return UserPublic.model_validate(target)


@router.patch(
    "/{user_id}/status",
    response_model=UserPublic,
    summary="Block or reactivate a user (admin+). Blocking revokes every session.",
)
async def admin_change_user_status(
    user_id: UUID,
    data: AdminUserStatusUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    target = await user_service.admin_change_status(db, admin, user_id, data.status)
    await db.commit()
    return UserPublic.model_validate(target)
