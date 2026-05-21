"""Withdrawal — an author's request to cash out their available balance.

State machine:

    requested ──admin approve──> approved ──processing──> completed
        │                            │
        ├── admin reject ────────────┴──> rejected
        └── author cancel (only while requested) ───> cancelled

``bank_details`` is a JSON snapshot at request time so future profile
edits don't rewrite history. ``processed_by`` records the admin who
moved the request out of ``requested``.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.author_profile import AuthorProfile
    from app.models.user import User


class WithdrawalStatus(enum.StrEnum):
    requested = "requested"
    approved = "approved"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"
    cancelled = "cancelled"


class Withdrawal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "withdrawals"

    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("author_profiles.id"),
        nullable=False,
        index=True,
    )

    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="UZS", server_default="UZS"
    )

    bank_details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    status: Mapped[WithdrawalStatus] = mapped_column(
        SAEnum(WithdrawalStatus, name="withdrawal_status"),
        nullable=False,
        default=WithdrawalStatus.requested,
        server_default=WithdrawalStatus.requested.value,
        index=True,
    )

    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    processed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    author: Mapped[AuthorProfile] = relationship()
    admin: Mapped[User | None] = relationship(foreign_keys=[processed_by])
