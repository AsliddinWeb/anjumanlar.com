"""Review-request category — admin-managed lookup table.

A request belongs to one category (e.g. "article", "dissertation", "study
guide", "textbook"). Names are multilingual JSONB so the picker can render
the right label per locale.

Soft-disabled rows (``is_active=false``) drop out of the public list but
keep their FK so historical requests still resolve.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.review_request import ReviewRequest


class ReviewCategory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_categories"

    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", index=True
    )

    requests: Mapped[list[ReviewRequest]] = relationship(
        back_populates="category", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<ReviewCategory {self.slug!r}>"
