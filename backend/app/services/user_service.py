"""User profile lifecycle — read it in three pieces:

1. ``update_profile``: copy-over of the optional fields the user can edit.
2. ``set_avatar``: hands the bytes to storage_service then patches the URL.
3. ``soft_delete``: marks status=deleted, anonymizes the email so it can be
   re-used by future registrations, and revokes every refresh token.

Side-effects (revoking sessions) reuse helpers from ``auth_service`` to avoid
duplicating logic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserStatus
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


async def soft_delete(db: AsyncSession, user: User) -> None:
    """Soft-delete the account so the email frees up for re-registration and
    every session dies. The row stays in the DB to preserve foreign-key
    integrity (orders, reviews, …)."""
    user_id: UUID = user.id
    now = datetime.now(UTC)

    user.status = UserStatus.deleted
    user.deleted_at = now
    user.email = f"deleted+{user_id}@anjumanlar.invalid"
    user.password_hash = ""  # disables password login for this row

    await logout_all(db, user_id)
    await db.flush()
