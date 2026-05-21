"""Author profile — extends a User into someone who can publish books.

Created via the "become author" flow (POST /api/v1/authors/me). A user has
at most one author_profile (1:1). When the user is fully deleted (rare —
soft delete is the default) the profile cascades. ``bank_details`` holds
withdrawal info; we never expose it on public endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class AuthorProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "author_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Multilingual: {"uz": "...", "ru": "...", "en": "..."}
    bio: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    academic_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    social_links: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # Sensitive — never returned by public endpoints.
    bank_details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    commission_rate: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=15.00, server_default="15.00"
    )
    total_sales: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    total_revenue: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0, server_default="0"
    )
    available_balance: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0, server_default="0"
    )
    pending_balance: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0, server_default="0"
    )

    verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="author_profile")
    books: Mapped[list[Book]] = relationship(back_populates="author", foreign_keys="Book.author_id")
