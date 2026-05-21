"""User library endpoints.

The library is read-only from the user's perspective — items only ever
arrive via ``library_service.grant_order`` on a paid order. The
download endpoint mints a short-lived presigned URL each time it's
called so a leaked link can't be reused once the TTL passes.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.library import (
    DownloadResponse,
    UserLibraryItem,
    UserLibraryList,
)
from app.services import library_service

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get(
    "/me",
    response_model=UserLibraryList,
    summary="List books in the current user's library",
)
async def list_my_library(
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> UserLibraryList:
    items, total = await library_service.list_for_user(
        db, user, page=page, page_size=page_size
    )
    return UserLibraryList(
        items=[UserLibraryItem.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/me/{book_id}/download",
    response_model=DownloadResponse,
    summary="Issue a short-lived signed URL for a book the user owns",
)
async def download_my_library_book(
    book_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> DownloadResponse:
    url, ttl = await library_service.issue_download_url(db, user, book_id)
    await db.commit()
    return DownloadResponse(url=url, expires_in=ttl)
