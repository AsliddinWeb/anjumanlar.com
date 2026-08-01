"""Publication type CRUD.

Flat list (no tree, unlike Category) — a book carries at most one via a
plain FK, so `book_count` is a straight COUNT(*) WHERE, not the
join-through-M2M query `category_service` needs.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Book, BookStatus, PublicationType
from app.schemas.publication_type import PublicationTypeCreate, PublicationTypeUpdate


async def list_all(db: AsyncSession, active_only: bool = True) -> list[PublicationType]:
    """All publication types with a live `book_count` (approved books
    only) — the same "compute on read" approach as `category_service`."""
    book_count = (
        select(func.count(Book.id))
        .where(
            Book.publication_type_id == PublicationType.id,
            Book.status == BookStatus.approved,
        )
        .correlate(PublicationType)
        .scalar_subquery()
    )

    stmt = select(PublicationType, book_count.label("live_book_count"))
    if active_only:
        stmt = stmt.where(PublicationType.is_active.is_(True))
    stmt = stmt.order_by(PublicationType.sort_order, PublicationType.slug)

    rows = (await db.execute(stmt)).all()
    types: list[PublicationType] = []
    for row, live_count in rows:
        row.book_count = int(live_count or 0)
        types.append(row)
    return types


async def get_by_slug(db: AsyncSession, slug: str) -> PublicationType:
    row = (
        await db.execute(select(PublicationType).where(PublicationType.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Publication type not found", details={"code": "publication_type_not_found"}
        )
    row.book_count = await _live_book_count(db, row.id)
    return row


async def get_by_id(db: AsyncSession, publication_type_id: UUID) -> PublicationType:
    row = (
        await db.execute(
            select(PublicationType).where(PublicationType.id == publication_type_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Publication type not found", details={"code": "publication_type_not_found"}
        )
    return row


async def _live_book_count(db: AsyncSession, publication_type_id: UUID) -> int:
    stmt = select(func.count(Book.id)).where(
        Book.publication_type_id == publication_type_id,
        Book.status == BookStatus.approved,
    )
    return int((await db.execute(stmt)).scalar() or 0)


async def create(db: AsyncSession, data: PublicationTypeCreate) -> PublicationType:
    row = PublicationType(
        slug=data.slug,
        name=data.name,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "A publication type with this slug already exists",
            details={"code": "slug_taken"},
        ) from exc
    await db.refresh(row)
    return row


async def update(
    db: AsyncSession, publication_type_id: UUID, data: PublicationTypeUpdate
) -> PublicationType:
    row = await get_by_id(db, publication_type_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Slug collision while updating publication type",
            details={"code": "slug_taken"},
        ) from exc
    await db.refresh(row)
    return row


async def delete(db: AsyncSession, publication_type_id: UUID) -> None:
    row = await get_by_id(db, publication_type_id)
    await db.delete(row)
    await db.flush()
