"""Blog posts — admin-authored articles, multilingual.

State machine: ``draft → published → archived``. Only ``published``
posts surface on the public ``/blog`` route. ``slug`` is unique; the
admin sets it explicitly (no auto-slugify) so editorial URLs stay
stable across title tweaks.

Body is plain markdown; rendering happens client-side via a tiny
``markdown-it`` instance on the frontend (no XSS-prone HTML on the
wire).
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class BlogPostStatus(enum.StrEnum):
    draft = "draft"
    published = "published"
    archived = "archived"


class BlogPost(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "blog_posts"

    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)

    # Multilingual ``{"uz": "...", "ru": "...", "en": "..."}``.
    title: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    excerpt: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    body: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[BlogPostStatus] = mapped_column(
        SAEnum(BlogPostStatus, name="blog_post_status"),
        nullable=False,
        default=BlogPostStatus.draft,
        server_default=BlogPostStatus.draft.value,
        index=True,
    )

    # The admin who created the row; not really an "author" in the
    # marketplace sense, just for the audit trail.
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    creator: Mapped[User | None] = relationship()
