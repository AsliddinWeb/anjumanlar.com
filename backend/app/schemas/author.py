"""Pydantic schemas for /authors endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BecomeAuthorRequest(BaseModel):
    """Payload to upgrade a reader into an author."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    bio: dict[str, str] | None = None  # {uz, ru, en}
    academic_title: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=255)
    website: HttpUrl | None = None


class AuthorProfileUpdate(BaseModel):
    """PATCH-style author profile update — every field optional."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    bio: dict[str, str] | None = None
    academic_title: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=255)
    website: HttpUrl | None = None
    social_links: dict[str, str] | None = None
    bank_details: dict[str, Any] | None = None  # only via /me, never public


class AuthorPublic(BaseModel):
    """Public-facing author profile — strips bank_details + balances."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    display_name: str
    bio: dict[str, Any]
    academic_title: str | None = None
    institution: str | None = None
    website: str | None = None
    social_links: dict[str, Any]
    verified: bool
    featured: bool
    total_sales: int
    created_at: datetime


class AuthorPrivate(AuthorPublic):
    """Author's own view of their profile — includes commission + balances
    but still hides ``bank_details`` until the dedicated payouts UI ships."""

    commission_rate: float
    total_revenue: float
    available_balance: float
    pending_balance: float


class AuthorList(BaseModel):
    items: list[AuthorPublic]
    total: int
    page: int
    page_size: int
