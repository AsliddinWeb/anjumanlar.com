"""Review endpoints — list/create (public/user), edit/delete (own),
admin moderation.

Routes split between two prefixes:

- ``/books/{book_id}/reviews``  → list + create
- ``/reviews/{review_id}``      → edit + delete + admin actions
- ``/admin/reviews``            → moderation queue

For clarity we register two routers (``books_review_router`` is mounted
inside ``books.py``-style and ``review_router`` is mounted at v1 root).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.models import ReviewStatus
from app.schemas.review import (
    ReviewAdminList,
    ReviewAdminView,
    ReviewCreate,
    ReviewList,
    ReviewPublic,
    ReviewUpdate,
)
from app.services import review_service

books_review_router = APIRouter(prefix="/books", tags=["reviews"])
review_router = APIRouter(prefix="/reviews", tags=["reviews"])
admin_review_router = APIRouter(prefix="/admin/reviews", tags=["reviews"])


# ---------- public list + create ----------


@books_review_router.get(
    "/{book_id}/reviews",
    response_model=ReviewList,
    summary="Approved reviews for a book",
)
async def list_book_reviews(
    book_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ReviewList:
    items, total = await review_service.list_for_book(db, book_id, page=page, page_size=page_size)
    return ReviewList(
        items=[ReviewPublic.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@books_review_router.post(
    "/{book_id}/reviews",
    response_model=ReviewPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review (lands in pending status pending moderation)",
)
async def create_book_review(
    book_id: UUID,
    data: ReviewCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewPublic:
    review = await review_service.create_review(db, user, book_id, data)
    await db.commit()
    return ReviewPublic.model_validate(review)


# ---------- author edit/delete ----------


@review_router.patch(
    "/{review_id}",
    response_model=ReviewPublic,
    summary="Edit your own review; sends it back to moderation",
)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewPublic:
    review = await review_service.update_review(db, user, review_id, data)
    await db.commit()
    return ReviewPublic.model_validate(review)


@review_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your own review (admins can delete anyone's)",
)
async def delete_review(
    review_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    await review_service.delete_review(db, user, review_id)
    await db.commit()


# ---------- admin moderation ----------


@admin_review_router.get(
    "",
    response_model=ReviewAdminList,
    summary="Admin review list — pending by default, filterable to any status",
)
async def admin_list_reviews(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReviewStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ReviewAdminList:
    items, total = await review_service.admin_list(
        db, page=page, page_size=page_size, status=status_filter
    )
    return ReviewAdminList(
        items=[ReviewAdminView.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_review_router.post(
    "/{review_id}/approve",
    response_model=ReviewAdminView,
    summary="Approve a review and recompute the book's rating aggregate",
)
async def approve_review(
    review_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> ReviewAdminView:
    review = await review_service.approve_review(db, admin, review_id)
    await db.commit()
    return ReviewAdminView.model_validate(review)


@admin_review_router.post(
    "/{review_id}/reject",
    response_model=ReviewAdminView,
    summary="Reject a review (kept in the table for audit)",
)
async def reject_review(
    review_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    _body: dict | None = Body(default=None),  # accept empty/extra body for now
    db: AsyncSession = Depends(get_db),
) -> ReviewAdminView:
    review = await review_service.reject_review(db, admin, review_id)
    await db.commit()
    return ReviewAdminView.model_validate(review)
