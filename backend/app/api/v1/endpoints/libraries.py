"""User library endpoints.

The library is read-only from the user's perspective — items only ever
arrive via ``library_service.grant_order`` on a paid order. The
download endpoint mints a short-lived presigned URL each time it's
called so a leaked link can't be reused once the TTL passes.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.integrations.minio_client import stat_object, stream_object
from app.models import User, UserLibrary
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


@router.get(
    "/me/{book_id}/stream",
    summary="Stream the user's watermarked PDF inline (online reader)",
)
async def stream_my_library_book(
    book_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Pipe the watermarked PDF to the browser as ``application/pdf``.

    Unlike the signed-URL endpoint this never exposes the MinIO object
    URL and never sets a ``Content-Disposition: attachment`` header — the
    browser opens the PDF inline so the PDF.js viewer can hand the bytes
    over to the user without offering a save dialog. We still check
    ownership on every request, so a leaked URL is no use once the
    session token expires.
    """
    owned = (
        await db.execute(
            select(UserLibrary.id).where(
                UserLibrary.user_id == user.id,
                UserLibrary.book_id == book_id,
            )
        )
    ).scalar_one_or_none()
    if owned is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_in_library", "message": "You don't own this book"},
        )

    object_key = f"{user.id}/{book_id}.pdf"
    try:
        info = stat_object(settings.MINIO_BUCKET_BOOKS_WM, object_key)
    except Exception as exc:  # noqa: BLE001 — MinIO surfaces a wide family of errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "watermark_not_ready", "message": "Watermarked copy not ready"},
        ) from exc

    return StreamingResponse(
        stream_object(settings.MINIO_BUCKET_BOOKS_WM, object_key),
        media_type="application/pdf",
        headers={
            "Content-Length": str(info.size),
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
