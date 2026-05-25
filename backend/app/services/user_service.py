"""User profile lifecycle — read it in three pieces:

1. ``update_profile``: copy-over of the optional fields the user can edit.
2. ``set_avatar``: hands the bytes to storage_service then patches the URL.
3. ``delete_user``: hard-deletes the row. Auth tokens / refresh tokens /
   author profile / reviews / library / wishlist all cascade. Books the
   user uploaded, orders, and withdrawals use RESTRICT — if any of those
   exist the delete refuses with a clear error.

Side-effects (revoking sessions) reuse helpers from ``auth_service`` to avoid
duplicating logic.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import User, UserRole, UserStatus
from app.schemas.auth import UserUpdate
from app.services import storage_service
from app.services.auth_service import logout_all


async def update_profile(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Apply the PATCH payload — only fields the client explicitly set."""
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def set_avatar(
    db: AsyncSession,
    user: User,
    raw: bytes,
    content_type: str,
) -> User:
    """Resize + push to MinIO + persist the URL."""
    url = storage_service.upload_avatar(user.id, raw, content_type)
    user.avatar_url = url
    await db.flush()
    await db.refresh(user)
    return user


async def admin_list(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
) -> tuple[list[User], int]:
    """Admin search across users. Filters compose AND."""
    base = select(User)
    if search:
        like = f"%{search.strip()}%"
        base = base.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if role is not None:
        base = base.where(User.role == role)
    if status is not None:
        base = base.where(User.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(User.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def _get(db: AsyncSession, user_id: UUID) -> User:
    row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if row is None:
        raise NotFoundError("User not found", details={"code": "user_not_found"})
    return row


def _assert_target_not_superadmin(target: User, actor: User) -> None:
    """Superadmin rows are append-only from the admin panel — only another
    superadmin (in DB-shell territory) can mutate them. This stops a
    regular admin from demoting/blocking the founder account.
    """
    if target.role == UserRole.superadmin and actor.role != UserRole.superadmin:
        raise ForbiddenError(
            "Cannot modify a superadmin", details={"code": "superadmin_protected"}
        )


async def admin_change_role(
    db: AsyncSession,
    actor: User,
    user_id: UUID,
    new_role: UserRole,
) -> User:
    target = await _get(db, user_id)
    if target.id == actor.id:
        raise ConflictError(
            "You can't change your own role", details={"code": "self_role_change"}
        )
    _assert_target_not_superadmin(target, actor)
    # Only a superadmin can mint another superadmin.
    if new_role == UserRole.superadmin and actor.role != UserRole.superadmin:
        raise ForbiddenError(
            "Only a superadmin can promote to superadmin",
            details={"code": "superadmin_required"},
        )
    target.role = new_role
    await db.flush()
    return target


async def admin_change_status(
    db: AsyncSession,
    actor: User,
    user_id: UUID,
    new_status: UserStatus,
) -> User:
    target = await _get(db, user_id)
    if target.id == actor.id:
        raise ConflictError(
            "You can't change your own status", details={"code": "self_status_change"}
        )
    _assert_target_not_superadmin(target, actor)

    target.status = new_status
    if new_status == UserStatus.blocked:
        await logout_all(db, target.id)
    await db.flush()
    return target


async def delete_user(db: AsyncSession, user: User) -> None:
    """Hard-delete the account. Cascading FKs (refresh_tokens, auth_tokens,
    author_profile, reviews, library, wishlist) clean up automatically.

    Refuses (with a friendly error) if RESTRICT-protected references
    still exist — books the user uploaded, orders, withdrawals — so the
    operator knows to deal with those first.
    """
    user_id: UUID = user.id

    await logout_all(db, user_id)
    await db.delete(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError(
            "Cannot delete a user that still has books, orders, or withdrawals.",
            details={"code": "user_has_dependents"},
        ) from exc


async def admin_delete_user(
    db: AsyncSession,
    actor: User,
    user_id: UUID,
) -> None:
    """Admin variant of :func:`delete_user` — same hard-delete semantics
    plus the usual self/superadmin guards."""
    target = await _get(db, user_id)
    if target.id == actor.id:
        raise ConflictError(
            "You can't delete your own account from here", details={"code": "self_delete"}
        )
    _assert_target_not_superadmin(target, actor)
    await delete_user(db, target)
