"""Category CRUD + tree assembly.

Categories are an adjacency list (``parent_id``). We materialise the tree
in Python rather than via a recursive CTE because the dataset is small
(< 200 nodes expected) and the public list is hit on every homepage
load — keeping the SQL straightforward.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def list_all(db: AsyncSession, active_only: bool = True) -> list[Category]:
    stmt = select(Category)
    if active_only:
        stmt = stmt.where(Category.is_active.is_(True))
    stmt = stmt.order_by(Category.sort_order, Category.slug)
    return list((await db.execute(stmt)).scalars().all())


async def list_tree(db: AsyncSession, active_only: bool = True) -> list[dict[str, Any]]:
    """Flat list → nested structure. Each node gets a ``children`` key."""
    rows = await list_all(db, active_only=active_only)

    nodes: dict[UUID, dict[str, Any]] = {}
    for row in rows:
        nodes[row.id] = {
            "id": row.id,
            "parent_id": row.parent_id,
            "slug": row.slug,
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "image_url": row.image_url,
            "sort_order": row.sort_order,
            "is_active": row.is_active,
            "book_count": row.book_count,
            "children": [],
        }

    roots: list[dict[str, Any]] = []
    for node in nodes.values():
        parent_id = node["parent_id"]
        if parent_id is None or parent_id not in nodes:
            roots.append(node)
        else:
            nodes[parent_id]["children"].append(node)
    return roots


async def get_by_slug(db: AsyncSession, slug: str) -> Category:
    row = (await db.execute(select(Category).where(Category.slug == slug))).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Category not found", details={"code": "category_not_found"})
    return row


async def get_by_id(db: AsyncSession, category_id: UUID) -> Category:
    row = (
        await db.execute(select(Category).where(Category.id == category_id))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Category not found", details={"code": "category_not_found"})
    return row


async def create(db: AsyncSession, data: CategoryCreate) -> Category:
    if data.parent_id is not None:
        # Validate parent exists; raises NotFoundError if missing.
        await get_by_id(db, data.parent_id)

    category = Category(
        slug=data.slug,
        name=data.name,
        description=data.description or {},
        icon=data.icon,
        image_url=data.image_url,
        parent_id=data.parent_id,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    db.add(category)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "A category with this slug already exists",
            details={"code": "slug_taken"},
        ) from exc
    await db.refresh(category)
    return category


async def update(db: AsyncSession, category_id: UUID, data: CategoryUpdate) -> Category:
    category = await get_by_id(db, category_id)
    updates = data.model_dump(exclude_unset=True)

    if "parent_id" in updates and updates["parent_id"] is not None:
        if updates["parent_id"] == category_id:
            raise ConflictError(
                "A category can't be its own parent",
                details={"code": "self_parent"},
            )
        await get_by_id(db, updates["parent_id"])

    for key, value in updates.items():
        setattr(category, key, value)

    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Slug collision while updating category",
            details={"code": "slug_taken"},
        ) from exc
    await db.refresh(category)
    return category


async def delete(db: AsyncSession, category_id: UUID) -> None:
    category = await get_by_id(db, category_id)
    await db.delete(category)
    await db.flush()
