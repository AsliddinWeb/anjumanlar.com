"""Single-use auth tokens (email verification + password reset).

Same opaque + hashed shape as refresh tokens, but with a `purpose` enum and a
`used_at` stamp so each token fires exactly once. After `used_at` is set, a
second attempt is rejected even before checking expiry.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuthTokenPurpose(enum.StrEnum):
    email_verification = "email_verification"
    password_reset = "password_reset"


class AuthToken(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "auth_tokens"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    purpose: Mapped[AuthTokenPurpose] = mapped_column(
        SAEnum(
            AuthTokenPurpose,
            name="auth_token_purpose",
            values_callable=lambda e: [v.value for v in e],
        ),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="auth_tokens")
