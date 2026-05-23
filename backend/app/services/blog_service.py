"""Blog post lifecycle.

State machine::

    draft ──publish──> published ──archive──> archived
       ▲                                          │
       └────────── unpublish ─────────────────────┘  (admin only)

Only ``published`` posts surface on the public ``/blog`` feed; admin
endpoints can pull any status.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import BlogPost, BlogPostStatus, User
from app.schemas.blog import BlogPostCreate, BlogPostUpdate


def _has_localised_value(payload: dict | None) -> bool:
    if not isinstance(payload, dict):
        return False
    return any(isinstance(v, str) and v.strip() for v in payload.values())


async def create(db: AsyncSession, actor: User, data: BlogPostCreate) -> BlogPost:
    if not _has_localised_value(data.title):
        raise ValidationError(
            "title must contain at least one non-empty locale",
            details={"code": "title_required"},
        )

    post = BlogPost(
        slug=data.slug,
        title=data.title,
        excerpt=data.excerpt or {},
        body=data.body or {},
        cover_url=data.cover_url,
        status=BlogPostStatus.draft,
        created_by=actor.id,
    )
    db.add(post)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Slug is already taken", details={"code": "slug_taken"}
        ) from exc
    await db.refresh(post)
    return post


async def get_by_id(db: AsyncSession, post_id: UUID) -> BlogPost:
    row = (
        await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Blog post not found", details={"code": "blog_post_not_found"}
        )
    return row


async def get_published_by_slug(db: AsyncSession, slug: str) -> BlogPost:
    row = (
        await db.execute(
            select(BlogPost).where(
                BlogPost.slug == slug, BlogPost.status == BlogPostStatus.published
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Blog post not found", details={"code": "blog_post_not_found"}
        )
    return row


async def update(
    db: AsyncSession, post_id: UUID, data: BlogPostUpdate
) -> BlogPost:
    post = await get_by_id(db, post_id)
    updates = data.model_dump(exclude_unset=True)
    if "title" in updates and not _has_localised_value(updates["title"]):
        raise ValidationError(
            "title must contain at least one non-empty locale",
            details={"code": "title_required"},
        )
    for key, value in updates.items():
        # Coerce None for the JSONB fields into an empty dict so we never
        # write SQL NULL into a NOT NULL column.
        if key in {"excerpt", "body"} and value is None:
            value = {}
        setattr(post, key, value)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Slug is already taken", details={"code": "slug_taken"}
        ) from exc
    await db.refresh(post)
    return post


async def publish(db: AsyncSession, post_id: UUID) -> BlogPost:
    post = await get_by_id(db, post_id)
    if post.status == BlogPostStatus.published:
        return post
    post.status = BlogPostStatus.published
    if post.published_at is None:
        post.published_at = datetime.now(UTC)
    await db.flush()
    return post


async def unpublish(db: AsyncSession, post_id: UUID) -> BlogPost:
    post = await get_by_id(db, post_id)
    if post.status != BlogPostStatus.published:
        raise ConflictError(
            "Only published posts can be unpublished",
            details={"code": "invalid_state", "current_status": post.status.value},
        )
    post.status = BlogPostStatus.draft
    await db.flush()
    return post


async def archive(db: AsyncSession, post_id: UUID) -> BlogPost:
    post = await get_by_id(db, post_id)
    post.status = BlogPostStatus.archived
    await db.flush()
    return post


async def delete(db: AsyncSession, post_id: UUID) -> None:
    post = await get_by_id(db, post_id)
    await db.delete(post)
    await db.flush()


async def list_public(
    db: AsyncSession, *, page: int, page_size: int
) -> tuple[list[BlogPost], int]:
    base = select(BlogPost).where(BlogPost.status == BlogPostStatus.published)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(BlogPost.published_at.desc().nullslast())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def admin_list(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: BlogPostStatus | None = None,
) -> tuple[list[BlogPost], int]:
    base = select(BlogPost)
    if status is not None:
        base = base.where(BlogPost.status == status)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(BlogPost.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total
