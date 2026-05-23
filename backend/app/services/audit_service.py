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

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def list_audit(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user_id: UUID | None = None,
    action: AuditAction | None = None,
) -> tuple[list[AuditLog], int]:
    """Admin-only audit feed. Newest first.

    Filters compose AND so you can drill down by user *and* action; both
    are optional. Result ordering is ``created_at DESC`` (the index on
    ``created_at`` keeps this cheap)."""
    base = select(AuditLog)
    if user_id is not None:
        base = base.where(AuditLog.user_id == user_id)
    if action is not None:
        base = base.where(AuditLog.action == action)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(AuditLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total
