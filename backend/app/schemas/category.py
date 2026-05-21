"""Pydantic schemas for /categories endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Admin-only create payload."""

    slug: str = Field(..., min_length=1, max_length=150)
    name: dict[str, str] = Field(..., description="Multilingual: {uz, ru, en}")
    description: dict[str, str] | None = None
    icon: str | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=500)
    parent_id: UUID | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    """Admin-only PATCH — every field optional."""

    slug: str | None = Field(default=None, min_length=1, max_length=150)
    name: dict[str, str] | None = None
    description: dict[str, str] | None = None
    icon: str | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=500)
    parent_id: UUID | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None = None
    slug: str
    name: dict[str, Any]
    description: dict[str, Any]
    icon: str | None = None
    image_url: str | None = None
    sort_order: int
    is_active: bool
    book_count: int


class CategoryTreeNode(CategoryPublic):
    children: list[CategoryTreeNode] = []


class CategoryList(BaseModel):
    items: list[CategoryPublic]
    total: int
