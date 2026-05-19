"""Append-only audit trail of security-sensitive events.

``user_id`` is nullable: failed logins record the IP + attempted email in
``metadata`` even when no matching user row exists. Existing rows survive
account deletion (``ON DELETE SET NULL``) because we want history to
outlast the user.
"""

from __future__ import annotations

import enum
from typing import Any
from uuid import UUID

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class AuditAction(enum.StrEnum):
    register = "register"
    email_verified = "email_verified"
    resend_verification = "resend_verification"

    login_success = "login_success"
    login_failed = "login_failed"
    logout = "logout"
    logout_all = "logout_all"

    password_changed = "password_changed"
    password_reset_requested = "password_reset_requested"
    password_reset_completed = "password_reset_completed"

    profile_updated = "profile_updated"
    avatar_uploaded = "avatar_uploaded"
    account_deleted = "account_deleted"


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(
            AuditAction,
            name="audit_action",
            values_callable=lambda e: [v.value for v in e],
        ),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # `meta` rather than `metadata` — SQLAlchemy reserves the latter.
    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
