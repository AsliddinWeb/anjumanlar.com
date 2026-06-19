"""Pydantic schemas for the review-category lookup table."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

LocalisedText = dict[str, str]


class ReviewCategoryCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: LocalisedText
    description: LocalisedText | None = None
    sort_order: int = 0
    is_active: bool = True


class ReviewCategoryUpdate(BaseModel):
    slug: str | None = Field(default=None, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: LocalisedText | None = None
    description: LocalisedText | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ReviewCategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: dict[str, Any]
    description: dict[str, Any]
    sort_order: int
    is_active: bool
    created_at: datetime


class ReviewCategoryList(BaseModel):
    items: list[ReviewCategoryPublic]
    total: int
