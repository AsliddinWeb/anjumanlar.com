"""Book endpoints — public reads, author CRUD, admin moderation.

Order of paths matters for FastAPI's router: ``/books/me`` etc. must be
declared before ``/books/{slug}`` so they don't get swallowed by the
slug matcher.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.dependencies import require_admin, require_author
from app.models import BookStatus, User
from app.schemas.book import (
    BookAdminCreate,
    BookCreate,
    BookList,
    BookOwnerList,
    BookOwnerView,
    BookPublic,
    BookRejectRequest,
    BookSortKey,
    BookUpdate,
    MessageResponse,
)
from app.services import author_service, book_service

router = APIRouter(prefix="/books", tags=["books"])


# ---------- Author own listing + create ----------


@router.get(
    "/me",
    response_model=BookOwnerList,
    summary="Author's own books (all statuses)",
)
async def list_my_books(
    user: Annotated[User, Depends(require_author)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BookStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> BookOwnerList:
    items, total = await book_service.list_my_books(
        db, user, page=page, page_size=page_size, status=status_filter
    )
    return BookOwnerList(
        items=[BookOwnerView.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=BookOwnerView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book in draft status",
)
async def create_book(
    data: BookCreate,
    user: Annotated[User, Depends(require_author)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    profile = await author_service.get_by_user_id(db, user.id)
    if profile is None:
        # Admin uploaded without author_profile — refuse for now; Phase 5
        # adds the "publish on behalf of" admin flow.
        raise ForbiddenError(
            "Create an author profile first (POST /api/v1/authors/me)",
            details={"code": "no_author_profile"},
        )
    book = await book_service.create_book(db, user, profile, data)
    await db.commit()
    return BookOwnerView.model_validate(book)


# ---------- Owner / admin single read ----------


@router.get(
    "/owner/{book_id}",
    response_model=BookOwnerView,
    summary="Author/admin single-book view — exposes status, rejection reason, file URL",
)
async def read_owner_book(
    book_id: UUID,
    user: Annotated[User, Depends(require_author)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    return BookOwnerView.model_validate(await book_service.get_for_owner(db, user, book_id))


# ---------- Public listing ----------


@router.get(
    "",
    response_model=BookList,
    summary="Public catalogue — only approved books",
)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=200),
    category: str | None = Query(None, description="Category slug"),
    author: str | None = Query(None, description="Author slug"),
    language: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    featured: bool | None = None,
    sort: BookSortKey = Query("-published_at"),
    db: AsyncSession = Depends(get_db),
) -> BookList:
    items, total = await book_service.list_public(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_slug=category,
        author_slug=author,
        language=language,
        min_price=min_price,
        max_price=max_price,
        featured=featured,
        sort=sort,
    )
    return BookList(
        items=[BookPublic.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------- Single book ----------


@router.get(
    "/{slug}",
    response_model=BookPublic,
    summary="Public book page (approved books only)",
)
async def read_book(slug: str, db: AsyncSession = Depends(get_db)) -> BookPublic:
    return BookPublic.model_validate(await book_service.get_public_by_slug(db, slug))


@router.patch(
    "/{book_id}",
    response_model=BookOwnerView,
    summary="Update a book (author only, draft/rejected status)",
)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    user: Annotated[User, Depends(require_author)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.update_book(db, user, book_id, data)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book (author or admin) — refuses if orders exist",
)
async def delete_book(
    book_id: UUID,
    user: Annotated[User, Depends(require_author)],
    db: AsyncSession = Depends(get_db),
) -> None:
    await book_service.delete_book(db, user, book_id)
    await db.commit()


@router.post(
    "/{book_id}/submit",
    response_model=BookOwnerView,
    summary="Submit a draft (or rejected) book for moderation",
)
async def submit_book(
    book_id: UUID,
    user: Annotated[User, Depends(require_author)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.submit_for_moderation(db, user, book_id)
    await db.commit()
    return BookOwnerView.model_validate(book)


# ---------- File uploads (cover + PDF) ----------


@router.post(
    "/{book_id}/cover",
    response_model=BookOwnerView,
    summary="Upload a book cover (resized to 800x1200 JPEG)",
)
async def upload_cover(
    book_id: UUID,
    user: Annotated[User, Depends(require_author)],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    raw = await file.read()
    book = await book_service.set_cover(
        db, user, book_id, raw, file.content_type or "application/octet-stream"
    )
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.post(
    "/{book_id}/file",
    response_model=BookOwnerView,
    summary="Upload the canonical PDF (extracts page count + file size)",
)
async def upload_book_file(
    book_id: UUID,
    user: Annotated[User, Depends(require_author)],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    raw = await file.read()
    book = await book_service.set_file(
        db, user, book_id, raw, file.content_type or "application/octet-stream"
    )
    await db.commit()
    return BookOwnerView.model_validate(book)


# ---------- Admin moderation + full CRUD ----------
#
# Mounted as /books/admin/* to keep the router single-file. Phase 5 may
# split these into a dedicated admin sub-router.


@router.get(
    "/admin/all",
    response_model=BookOwnerList,
    summary="Full admin catalogue — every book regardless of status (admin+)",
)
async def admin_list_all(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BookStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, min_length=1, max_length=200),
    author_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> BookOwnerList:
    items, total = await book_service.admin_list_all(
        db,
        page=page,
        page_size=page_size,
        status=status_filter,
        search=search,
        author_id=author_id,
    )
    return BookOwnerList(
        items=[BookOwnerView.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/admin",
    response_model=BookOwnerView,
    status_code=status.HTTP_201_CREATED,
    summary="Admin creates a book on behalf of any author (admin+)",
)
async def admin_create_book(
    data: BookAdminCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.admin_create_book(db, admin, data.author_id, data)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.patch(
    "/admin/{book_id}",
    response_model=BookOwnerView,
    summary="Admin edit — any status, any field (admin+)",
)
async def admin_patch_book(
    book_id: UUID,
    data: BookUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.admin_update_book(db, admin, book_id, data)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.get(
    "/admin/moderation",
    response_model=BookList,
    summary="Books awaiting moderation (admin+)",
)
async def admin_list_moderation(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BookList:
    items, total = await book_service.list_moderation_queue(db, page=page, page_size=page_size)
    return BookList(
        items=[BookPublic.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/admin/{book_id}/publish",
    response_model=BookOwnerView,
    summary="Admin shortcut — publish a draft / rejected / pending book straight away",
)
async def admin_publish_book_endpoint(
    book_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.admin_publish_book(db, admin, book_id)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.post(
    "/admin/{book_id}/unpublish",
    response_model=BookOwnerView,
    summary="Admin shortcut — pull an approved book back to draft (hides it)",
)
async def admin_unpublish_book_endpoint(
    book_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.admin_unpublish_book(db, admin, book_id)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.post(
    "/admin/{book_id}/approve",
    response_model=BookOwnerView,
    summary="Approve a pending book (admin+)",
)
async def admin_approve_book(
    book_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.approve(db, admin, book_id)
    await db.commit()
    return BookOwnerView.model_validate(book)


@router.post(
    "/admin/{book_id}/reject",
    response_model=BookOwnerView,
    summary="Reject a pending book with a reason (admin+)",
)
async def admin_reject_book(
    book_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    data: BookRejectRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> BookOwnerView:
    book = await book_service.reject(db, admin, book_id, data.reason)
    await db.commit()
    return BookOwnerView.model_validate(book)


__all__ = ["MessageResponse", "router"]
