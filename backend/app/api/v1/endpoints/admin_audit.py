"""Admin-only audit log feed.

Read-only by design: audit rows are written from ``audit_service`` and
should never be edited from the API surface. Filterable by user and
action; pagination defaults match the other admin queues.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import AuditAction, User
from app.schemas.audit import AuditLogList, AuditLogPublic
from app.services import audit_service

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


@router.get(
    "",
    response_model=AuditLogList,
    summary="Audit log feed (admin+), newest first",
)
async def list_audit_logs(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: UUID | None = None,
    action: AuditAction | None = None,
    db: AsyncSession = Depends(get_db),
) -> AuditLogList:
    items, total = await audit_service.list_audit(
        db, page=page, page_size=page_size, user_id=user_id, action=action
    )
    return AuditLogList(
        items=[AuditLogPublic.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )
