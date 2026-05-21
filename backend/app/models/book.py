"""Book (monograph) — the central product entity.

Two distinct user references:

- ``author_id`` (FK author_profiles) — who the book is *by*. Used for
  payouts and "author's catalog" listings.
- ``uploaded_by`` (FK users) — who pushed the upload button. Usually
  the author themself, but admins/staff can upload on behalf of an
  institution that doesn't have its own account.

``is_free`` is a generated column (price = 0), so a single index handles
"free books" listings.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.author_profile import AuthorProfile
    from app.models.category import Category
    from app.models.review import Review
    from app.models.user import User


class BookStatus(enum.StrEnum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


class BookLanguage(enum.StrEnum):
    uz = "uz"
    ru = "ru"
    en = "en"
    mixed = "mixed"


class Book(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "books"

    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("author_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Multilingual JSONB: {"uz": "...", "ru": "...", "en": "..."}
    title: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    subtitle: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    description: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[BookLanguage] = mapped_column(
        SAEnum(BookLanguage, name="book_language", values_callable=lambda e: [v.value for v in e]),
        nullable=False,
        default=BookLanguage.uz,
        server_default="uz",
    )
    pages_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_mb: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # private original
    demo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # public preview

    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)

    price: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    discount_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Generated column — Postgres recomputes it whenever price changes.
    is_free: Mapped[bool] = mapped_column(
        Boolean, Computed("(price = 0)", persisted=True), nullable=False
    )

    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="book_status", values_callable=lambda e: [v.value for v in e]),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    views_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    downloads_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    sales_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    average_rating: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0, server_default="0"
    )
    reviews_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    seo_title: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    seo_description: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, server_default="{}"
    )

    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    author: Mapped[AuthorProfile] = relationship(back_populates="books", foreign_keys=[author_id])
    uploader: Mapped[User] = relationship(foreign_keys=[uploaded_by])
    categories: Mapped[list[Category]] = relationship(
        secondary="book_categories", back_populates="books"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="book", cascade="all, delete-orphan", passive_deletes=True
    )
