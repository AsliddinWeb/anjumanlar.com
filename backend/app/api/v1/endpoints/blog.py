"""Blog endpoints.

Two routers:

- ``router`` — public read-only feed at ``/blog`` (mounted under v1).
- ``admin_router`` — admin CRUD + state transitions at ``/admin/blog``.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import BlogPostStatus, User
from app.schemas.blog import (
    BlogPostAdminList,
    BlogPostAdminView,
    BlogPostCreate,
    BlogPostList,
    BlogPostPublic,
    BlogPostUpdate,
)
from app.services import blog_service

router = APIRouter(prefix="/blog", tags=["blog"])
admin_router = APIRouter(prefix="/admin/blog", tags=["admin-blog"])


# ---------- public ----------


@router.get(
    "",
    response_model=BlogPostList,
    summary="Published blog posts, newest first",
)
async def list_published_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BlogPostList:
    items, total = await blog_service.list_public(db, page=page, page_size=page_size)
    return BlogPostList(
        items=[BlogPostPublic.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{slug}",
    response_model=BlogPostPublic,
    summary="One published post by slug",
)
async def read_post(slug: str, db: AsyncSession = Depends(get_db)) -> BlogPostPublic:
    return BlogPostPublic.model_validate(
        await blog_service.get_published_by_slug(db, slug)
    )


# ---------- admin ----------


@admin_router.get(
    "",
    response_model=BlogPostAdminList,
    summary="List blog posts (admin+, any status)",
)
async def admin_list_posts(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BlogPostStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminList:
    items, total = await blog_service.admin_list(
        db, page=page, page_size=page_size, status=status_filter
    )
    return BlogPostAdminList(
        items=[BlogPostAdminView.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.post(
    "",
    response_model=BlogPostAdminView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft post",
)
async def admin_create_post(
    data: BlogPostCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminView:
    post = await blog_service.create(db, admin, data)
    await db.commit()
    return BlogPostAdminView.model_validate(post)


@admin_router.get(
    "/{post_id}",
    response_model=BlogPostAdminView,
    summary="Read one post (admin)",
)
async def admin_read_post(
    post_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminView:
    return BlogPostAdminView.model_validate(await blog_service.get_by_id(db, post_id))


@admin_router.patch(
    "/{post_id}",
    response_model=BlogPostAdminView,
    summary="Edit a post (admin)",
)
async def admin_update_post(
    post_id: UUID,
    data: BlogPostUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminView:
    post = await blog_service.update(db, post_id, data)
    await db.commit()
    return BlogPostAdminView.model_validate(post)


@admin_router.post(
    "/{post_id}/publish",
    response_model=BlogPostAdminView,
    summary="Publish a draft (sets published_at on first publish)",
)
async def admin_publish_post(
    post_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminView:
    post = await blog_service.publish(db, post_id)
    await db.commit()
    return BlogPostAdminView.model_validate(post)


@admin_router.post(
    "/{post_id}/unpublish",
    response_model=BlogPostAdminView,
    summary="Move a published post back to draft",
)
async def admin_unpublish_post(
    post_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BlogPostAdminView:
    post = await blog_service.unpublish(db, post_id)
    await db.commit()
    return BlogPostAdminView.model_validate(post)


@admin_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a blog post (admin)",
)
async def admin_delete_post(
    post_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> None:
    await blog_service.delete(db, post_id)
    await db.commit()
