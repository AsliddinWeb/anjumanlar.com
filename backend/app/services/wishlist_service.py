"""Wishlist add/remove/list.

Each row is a (user, book) pair — duplicates are blocked by the UNIQUE
constraint on the model, but we also pre-check so we can return a clean
409 instead of a generic IntegrityError.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Book, BookStatus, User, Wishlist


async def _get_visible_book(db: AsyncSession, book_id: UUID) -> Book:
    book = (
        await db.execute(
            select(Book).where(
                Book.id == book_id,
                Book.status == BookStatus.approved,
                Book.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found", details={"code": "book_not_found"})
    return book


async def add(db: AsyncSession, user: User, book_id: UUID) -> Wishlist:
    await _get_visible_book(db, book_id)
    existing = (
        await db.execute(
            select(Wishlist).where(Wishlist.user_id == user.id, Wishlist.book_id == book_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(
            "Book is already on your wishlist",
            details={"code": "already_wished"},
        )

    row = Wishlist(user_id=user.id, book_id=book_id)
    db.add(row)
    await db.flush()
    return await _get_loaded(db, row.id)


async def remove(db: AsyncSession, user: User, book_id: UUID) -> None:
    row = (
        await db.execute(
            select(Wishlist).where(Wishlist.user_id == user.id, Wishlist.book_id == book_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Book is not on your wishlist",
            details={"code": "not_on_wishlist"},
        )
    await db.delete(row)
    await db.flush()


async def list_for_user(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
) -> tuple[list[Wishlist], int]:
    base = (
        select(Wishlist)
        .options(
            selectinload(Wishlist.book).selectinload(Book.author),
            selectinload(Wishlist.book).selectinload(Book.categories),
        )
        .join(Book, Wishlist.book_id == Book.id)
        .where(
            Wishlist.user_id == user.id,
            Book.status == BookStatus.approved,
            Book.deleted_at.is_(None),
        )
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(Wishlist.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def _get_loaded(db: AsyncSession, wishlist_id: UUID) -> Wishlist:
    return (
        await db.execute(
            select(Wishlist)
            .options(
                selectinload(Wishlist.book).selectinload(Book.author),
                selectinload(Wishlist.book).selectinload(Book.categories),
            )
            .where(Wishlist.id == wishlist_id)
        )
    ).scalar_one()
