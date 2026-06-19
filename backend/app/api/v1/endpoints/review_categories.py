"""Review-request category endpoints.

Two routers: a public read-only list for the request form, and an admin
CRUD router for `/admin/review-categories`.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas.review_category import (
    ReviewCategoryCreate,
    ReviewCategoryList,
    ReviewCategoryPublic,
    ReviewCategoryUpdate,
)
from app.services import review_category_service

public_router = APIRouter(prefix="/review-categories", tags=["review-categories"])
admin_router = APIRouter(
    prefix="/admin/review-categories", tags=["review-categories"]
)


@public_router.get(
    "",
    response_model=ReviewCategoryList,
    summary="Active review-request categories (public)",
)
async def list_public_categories(
    db: AsyncSession = Depends(get_db),
) -> ReviewCategoryList:
    rows = await review_category_service.list_public(db)
    return ReviewCategoryList(
        items=[ReviewCategoryPublic.model_validate(r) for r in rows],
        total=len(rows),
    )


@admin_router.get(
    "",
    response_model=ReviewCategoryList,
    summary="All review-request categories (admin)",
)
async def admin_list_categories(
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> ReviewCategoryList:
    rows, total = await review_category_service.list_admin(db)
    return ReviewCategoryList(
        items=[ReviewCategoryPublic.model_validate(r) for r in rows],
        total=total,
    )


@admin_router.post(
    "",
    response_model=ReviewCategoryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review-request category",
)
async def admin_create_category(
    data: ReviewCategoryCreate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> ReviewCategoryPublic:
    row = await review_category_service.create(db, data)
    await db.commit()
    return ReviewCategoryPublic.model_validate(row)


@admin_router.patch(
    "/{category_id}",
    response_model=ReviewCategoryPublic,
    summary="Edit a review-request category",
)
async def admin_update_category(
    category_id: UUID,
    data: ReviewCategoryUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> ReviewCategoryPublic:
    row = await review_category_service.update(db, category_id, data)
    await db.commit()
    return ReviewCategoryPublic.model_validate(row)


@admin_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review-request category",
)
async def admin_delete_category(
    category_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> None:
    await review_category_service.delete(db, category_id)
    await db.commit()
