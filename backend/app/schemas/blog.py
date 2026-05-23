"""Pydantic schemas for /blog (public) + /admin/blog (admin)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import BlogPostStatus

LocalisedText = dict[str, str]


class BlogPostCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=180)
    title: LocalisedText = Field(..., description="At least one locale required")
    excerpt: LocalisedText | None = None
    body: LocalisedText | None = None
    cover_url: str | None = Field(default=None, max_length=500)


class BlogPostUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    title: LocalisedText | None = None
    excerpt: LocalisedText | None = None
    body: LocalisedText | None = None
    cover_url: str | None = Field(default=None, max_length=500)


class BlogPostPublic(BaseModel):
    """Public-facing post — only ``published`` rows surface here."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: dict[str, Any]
    excerpt: dict[str, Any]
    body: dict[str, Any]
    cover_url: str | None = None
    published_at: datetime | None = None
    created_at: datetime


class BlogPostAdminView(BlogPostPublic):
    """Admin payload exposes the status field."""

    status: BlogPostStatus


class BlogPostList(BaseModel):
    items: list[BlogPostPublic]
    total: int
    page: int
    page_size: int


class BlogPostAdminList(BaseModel):
    items: list[BlogPostAdminView]
    total: int
    page: int
    page_size: int
