"""Pydantic schemas for /publication-types endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PublicationTypeCreate(BaseModel):
    """Admin-only create payload."""

    slug: str = Field(..., min_length=1, max_length=100)
    name: dict[str, str] = Field(..., description="Multilingual: {uz, ru, en}")
    sort_order: int = 0
    is_active: bool = True


class PublicationTypeUpdate(BaseModel):
    """Admin-only PATCH — every field optional."""

    slug: str | None = Field(default=None, min_length=1, max_length=100)
    name: dict[str, str] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class PublicationTypePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: dict[str, Any]
    sort_order: int
    is_active: bool
    book_count: int = 0


class PublicationTypeList(BaseModel):
    items: list[PublicationTypePublic]
    total: int
