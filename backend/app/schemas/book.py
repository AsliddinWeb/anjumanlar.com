"""Pydantic schemas for /books + /admin/books endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import BookLanguage, BookStatus

# Multilingual ``{"uz": "...", "ru": "...", "en": "..."}`` payload.
LocalisedText = dict[str, str]

PriceField = Annotated[float, Field(ge=0, le=1_000_000_000)]


# ----- Author write paths -----


class BookCreate(BaseModel):
    """Author payload for POST /books — creates a draft."""

    title: LocalisedText = Field(..., description="At least one locale required")
    subtitle: LocalisedText | None = None
    description: LocalisedText | None = None
    language: BookLanguage = BookLanguage.uz
    isbn: str | None = Field(default=None, max_length=20)
    publication_year: int | None = Field(default=None, ge=1500, le=2100)
    publisher: str | None = Field(default=None, max_length=255)
    price: PriceField = 0
    discount_price: PriceField | None = None
    category_ids: list[UUID] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list, max_length=20)

    def _localised_has_content(self) -> bool:
        return any(v.strip() for v in self.title.values() if isinstance(v, str))


class BookUpdate(BaseModel):
    """Author PATCH payload (draft/rejected status only)."""

    title: LocalisedText | None = None
    subtitle: LocalisedText | None = None
    description: LocalisedText | None = None
    language: BookLanguage | None = None
    isbn: str | None = Field(default=None, max_length=20)
    publication_year: int | None = Field(default=None, ge=1500, le=2100)
    publisher: str | None = Field(default=None, max_length=255)
    price: PriceField | None = None
    discount_price: PriceField | None = None
    category_ids: list[UUID] | None = None
    keywords: list[str] | None = Field(default=None, max_length=20)


class BookAdminCreate(BookCreate):
    """Admin payload for POST /books/admin — same fields plus an
    explicit ``author_id`` so the admin can attribute the book to any
    author profile (the author-self path takes the profile from the
    caller, which admins typically don't have)."""

    author_id: UUID


# ----- Read paths -----


class BookCategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: dict[str, Any]


class BookAuthorRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    display_name: str


class BookPublic(BaseModel):
    """Public-facing book view — only ``approved`` rows are ever exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: dict[str, Any]
    subtitle: dict[str, Any]
    description: dict[str, Any]
    language: BookLanguage
    isbn: str | None = None
    pages_count: int | None = None
    cover_url: str | None = None
    demo_url: str | None = None
    publication_year: int | None = None
    publisher: str | None = None

    price: float
    discount_price: float | None = None
    is_free: bool

    average_rating: float
    reviews_count: int
    views_count: int
    sales_count: int

    featured: bool
    published_at: datetime | None = None
    created_at: datetime

    author: BookAuthorRef
    categories: list[BookCategoryRef]


class BookOwnerView(BookPublic):
    """Author's view of their own book — exposes ``status`` and rejection
    reason, plus internal counters they should care about."""

    status: BookStatus
    rejection_reason: str | None = None
    file_url: str | None = None
    keywords: list[str]


class BookList(BaseModel):
    items: list[BookPublic]
    total: int
    page: int
    page_size: int


class BookOwnerList(BaseModel):
    items: list[BookOwnerView]
    total: int
    page: int
    page_size: int


# ----- Admin moderation -----


class BookRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    message: str


# ----- Filters (used as query params) -----


BookSortKey = Literal[
    "created_at",
    "-created_at",
    "price",
    "-price",
    "-average_rating",
    "-views_count",
    "-sales_count",
    "published_at",
    "-published_at",
]
