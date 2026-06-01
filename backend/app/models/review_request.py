"""Paid peer-review request.

A reader uploads a manuscript and asks a specific AuthorProfile to
review it. The author then proposes a final price; the reader pays;
the author writes the review (text + optional supporting file); the
reader downloads it. Admin can oversee + refund.

State machine
-------------

    pending  ──quote──>  quoted  ──pay──>  paid  ──submit──>  completed
        │                   │                                   ▲
        └─────── cancel ────┴───── cancel ────────── (terminal) ┘

- ``pending``   — reader created, awaiting author quote.
- ``quoted``    — author set ``final_price``, awaiting payment.
- ``paid``      — payment confirmed, author can write the review.
- ``completed`` — author submitted review text (+ optional file).
- ``cancelled`` — either side withdrew before payment; admin can also
                  cancel post-payment which counts as a refund signal.

Payment integration is intentionally minimal in this first cut: the
admin (or a future Payme webhook) flips ``paid_at`` and the state
moves forward. Phase J wires Payme proper.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.author_profile import AuthorProfile
    from app.models.user import User


class ReviewRequestStatus(enum.StrEnum):
    pending = "pending"
    quoted = "quoted"
    paid = "paid"
    completed = "completed"
    cancelled = "cancelled"


class ReviewRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_requests"

    requester_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("author_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Manuscript (the work being reviewed) — uploaded after row creation.
    manuscript_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    manuscript_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Optional context from the requester (rich text-ish, stored as plain).
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ReviewRequestStatus] = mapped_column(
        SAEnum(
            ReviewRequestStatus,
            name="review_request_status",
            values_callable=lambda e: [v.value for v in e],
        ),
        nullable=False,
        default=ReviewRequestStatus.pending,
        server_default="pending",
        index=True,
    )

    # Optional budget proposed by the requester (display-only).
    proposed_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Final price set by the author — this is what the requester pays.
    final_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Author's response.
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Cancellation reason (visible to the requester when status=cancelled).
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle timestamps — handy for analytics + "took N days to
    # review" UI bits.
    quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    author: Mapped[AuthorProfile] = relationship(foreign_keys=[author_id])

    def __repr__(self) -> str:
        return f"<ReviewRequest {self.id} status={self.status.value}>"
