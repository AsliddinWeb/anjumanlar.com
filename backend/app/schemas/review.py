"""Pydantic schemas for /books/{id}/reviews + /reviews + admin moderation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ReviewStatus


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    body: str = Field(..., min_length=1, max_length=5000)


class ReviewUpdate(BaseModel):
    """Author can edit their own review while it's still pending; once
    approved further edits flip it back to pending for re-moderation."""

    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, min_length=1, max_length=5000)


class ReviewRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)


class ReviewAuthorRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    avatar_url: str | None = None


class ReviewPublic(BaseModel):
    """Public-facing review — strips moderation fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    rating: int
    title: str | None = None
    body: str
    helpful_count: int
    created_at: datetime
    user: ReviewAuthorRef


class ReviewAdminView(ReviewPublic):
    """Admin-only payload that also exposes the status field."""

    status: ReviewStatus


class ReviewList(BaseModel):
    items: list[ReviewPublic]
    total: int
    page: int
    page_size: int


class ReviewAdminList(BaseModel):
    items: list[ReviewAdminView]
    total: int
    page: int
    page_size: int
