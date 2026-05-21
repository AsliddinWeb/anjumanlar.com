"""Category endpoints — public reads, admin writes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas.category import (
    CategoryCreate,
    CategoryList,
    CategoryPublic,
    CategoryTreeNode,
    CategoryUpdate,
)
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=CategoryList,
    summary="Flat category list (sorted)",
)
async def list_categories(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> CategoryList:
    rows = await category_service.list_all(db, active_only=active_only)
    return CategoryList(
        items=[CategoryPublic.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.get(
    "/tree",
    response_model=list[CategoryTreeNode],
    summary="Nested category tree built from parent_id",
)
async def list_category_tree(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    # Service returns plain dicts already shaped for CategoryTreeNode.
    return await category_service.list_tree(db, active_only=active_only)


@router.get(
    "/{slug}",
    response_model=CategoryPublic,
    summary="Get one category by slug",
)
async def read_category(slug: str, db: AsyncSession = Depends(get_db)) -> CategoryPublic:
    return CategoryPublic.model_validate(await category_service.get_by_slug(db, slug))


@router.post(
    "",
    response_model=CategoryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category (admin+)",
)
async def create_category(
    data: CategoryCreate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> CategoryPublic:
    category = await category_service.create(db, data)
    await db.commit()
    return CategoryPublic.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryPublic,
    summary="Update a category (admin+)",
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> CategoryPublic:
    category = await category_service.update(db, category_id, data)
    await db.commit()
    return CategoryPublic.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category (admin+); children become roots via ON DELETE SET NULL",
)
async def delete_category(
    category_id: UUID,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> None:
    await category_service.delete(db, category_id)
    await db.commit()
