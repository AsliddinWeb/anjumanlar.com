"""Author profile lifecycle.

``become_author`` is the privilege-escalation step a reader takes when
they want to publish books. We:

1. Upgrade ``user.role`` from reader → author (admins/superadmins keep
   their existing role).
2. Create the matching ``author_profile`` row, deriving a URL slug from
   the display name. Conflicts get a numeric suffix.
3. Refuse if the user already has an author_profile (1:1).

Profile updates from /authors/me go through ``update_profile``. Public
endpoints query via ``get_public`` / ``list_public`` which keep blocked
or deleted users hidden.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import AuthorProfile, User, UserRole, UserStatus
from app.schemas.author import AuthorProfileUpdate, BecomeAuthorRequest


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """Return a slug guaranteed not to collide with existing author_profiles."""
    candidate = slugify(base) or "author"
    n = 0
    while True:
        suffix = f"-{n}" if n else ""
        slug = f"{candidate}{suffix}"[:150]
        exists = await db.execute(select(AuthorProfile.id).where(AuthorProfile.slug == slug))
        if exists.scalar_one_or_none() is None:
            return slug
        n += 1


async def become_author(db: AsyncSession, user: User, data: BecomeAuthorRequest) -> AuthorProfile:
    # Explicit query rather than ``user.author_profile`` — async lazy-loading
    # needs a greenlet context that isn't always available from the endpoint.
    existing = await get_by_user_id(db, user.id)
    if existing is not None:
        raise ConflictError("User is already an author", details={"code": "already_author"})

    if user.role == UserRole.reader:
        user.role = UserRole.author

    display_name = (data.display_name or user.full_name).strip()
    slug = await _unique_slug(db, display_name)

    profile = AuthorProfile(
        user_id=user.id,
        slug=slug,
        display_name=display_name,
        bio=data.bio or {},
        academic_title=data.academic_title,
        institution=data.institution,
        website=str(data.website) if data.website else None,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def get_me(db: AsyncSession, user: User) -> AuthorProfile:
    profile = await get_by_user_id(db, user.id)
    if profile is None:
        raise NotFoundError("User has no author profile", details={"code": "not_author"})
    return profile


async def update_profile(db: AsyncSession, user: User, data: AuthorProfileUpdate) -> AuthorProfile:
    profile = await get_me(db, user)
    updates: dict[str, Any] = data.model_dump(exclude_unset=True)
    # Coerce HttpUrl → str so SQLAlchemy/asyncpg can persist it.
    if "website" in updates and updates["website"] is not None:
        updates["website"] = str(updates["website"])
    for key, value in updates.items():
        setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def get_public_by_slug(db: AsyncSession, slug: str) -> AuthorProfile:
    """Look up by slug; hide profiles whose owner is blocked/deleted."""
    row = await db.execute(
        select(AuthorProfile)
        .join(User, AuthorProfile.user_id == User.id)
        .where(
            AuthorProfile.slug == slug,
            User.status != UserStatus.blocked,
        )
    )
    profile = row.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Author not found", details={"code": "author_not_found"})
    return profile


async def list_public(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    featured: bool | None = None,
) -> tuple[list[AuthorProfile], int]:
    base = (
        select(AuthorProfile)
        .join(User, AuthorProfile.user_id == User.id)
        .where(User.status != UserStatus.blocked)
    )
    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                AuthorProfile.display_name.ilike(like),
                AuthorProfile.institution.ilike(like),
            )
        )
    if featured is not None:
        base = base.where(AuthorProfile.featured.is_(featured))

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    items = (
        (
            await db.execute(
                base.order_by(AuthorProfile.featured.desc(), AuthorProfile.total_sales.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(items), total


async def get_by_user_id(db: AsyncSession, user_id: UUID) -> AuthorProfile | None:
    """Service helper — used when other code (book service) needs the
    profile for the calling user."""
    return (
        await db.execute(select(AuthorProfile).where(AuthorProfile.user_id == user_id))
    ).scalar_one_or_none()
