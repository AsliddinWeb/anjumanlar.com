"""Append-only audit log writes.

Each call opens its own session and commits independently of the caller's
transaction. Two reasons:

1. ``login_failed`` must be recorded even when the request transaction is
   about to error out — sharing the session would lose those rows on
   rollback.
2. Audit writes never block the user's action. If the audit insert fails
   we log and swallow rather than break the API call.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.models import AuditAction, AuditLog

logger = logging.getLogger(__name__)


async def log_event(
    action: AuditAction,
    *,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                AuditLog(
                    user_id=user_id,
                    action=action,
                    ip_address=ip_address,
                    user_agent=user_agent[:500] if user_agent else None,
                    meta=meta or {},
                )
            )
            await session.commit()
    except Exception:
        logger.exception("audit_log write failed: action=%s user_id=%s", action.value, user_id)
