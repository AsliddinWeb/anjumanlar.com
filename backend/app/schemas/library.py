"""Pydantic schemas for /libraries/me endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.book import BookPublic


class UserLibraryItem(BaseModel):
    """A purchased book in the user's library."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book: BookPublic
    watermarked_url: str | None = None
    downloaded_count: int
    last_downloaded_at: datetime | None = None
    acquired_at: datetime


class UserLibraryList(BaseModel):
    items: list[UserLibraryItem]
    total: int
    page: int
    page_size: int


class DownloadResponse(BaseModel):
    """Short-lived presigned URL for the watermarked PDF."""

    url: str
    expires_in: int
