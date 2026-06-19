"""Admin-managed review-request category lookup."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import ReviewCategory
from app.schemas.review_category import ReviewCategoryCreate, ReviewCategoryUpdate


async def list_public(db: AsyncSession) -> list[ReviewCategory]:
    """Categories visible to end-users — active rows only, sort order then slug."""
    rows = (
        await db.execute(
            select(ReviewCategory)
            .where(ReviewCategory.is_active.is_(True))
            .order_by(ReviewCategory.sort_order.asc(), ReviewCategory.slug.asc())
        )
    ).scalars().all()
    return list(rows)


async def list_admin(db: AsyncSession) -> tuple[list[ReviewCategory], int]:
    rows = (
        await db.execute(
            select(ReviewCategory).order_by(
                ReviewCategory.sort_order.asc(), ReviewCategory.slug.asc()
            )
        )
    ).scalars().all()
    total = (
        await db.execute(select(func.count()).select_from(ReviewCategory))
    ).scalar_one()
    return list(rows), total


async def get(db: AsyncSession, category_id: UUID) -> ReviewCategory:
    row = (
        await db.execute(select(ReviewCategory).where(ReviewCategory.id == category_id))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Category not found", details={"code": "review_category_not_found"}
        )
    return row


async def create(db: AsyncSession, data: ReviewCategoryCreate) -> ReviewCategory:
    row = ReviewCategory(
        slug=data.slug,
        name=data.name,
        description=data.description or {},
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Category slug already exists", details={"code": "slug_taken"}
        ) from exc
    return row


async def update(
    db: AsyncSession, category_id: UUID, data: ReviewCategoryUpdate
) -> ReviewCategory:
    row = await get(db, category_id)
    updates: dict[str, Any] = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Category slug already exists", details={"code": "slug_taken"}
        ) from exc
    return row


async def delete(db: AsyncSession, category_id: UUID) -> None:
    row = await get(db, category_id)
    await db.delete(row)
    await db.flush()
