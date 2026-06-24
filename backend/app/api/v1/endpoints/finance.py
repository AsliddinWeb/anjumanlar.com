"""Finance analytics endpoints.

Two surfaces:

- ``/admin/finance`` — admin-only rollup for the finance dashboard
  (KPIs, daily series, top books/authors, status mix).
- ``/finance/me`` — author-only earnings dashboard (last-30d series +
  lifetime totals + their top 5 books).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.services import finance_service

router = APIRouter(prefix="/admin/finance", tags=["finance"])
author_router = APIRouter(prefix="/finance", tags=["finance"])


@router.get(
    "/overview",
    summary="Admin finance overview (KPIs + series + top tables)",
)
async def admin_finance_overview(
    _: Annotated[User, Depends(require_admin)],
    days: int = Query(30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await finance_service.admin_overview(db, days=days)


@author_router.get(
    "/me",
    summary="Author earnings overview (series + totals)",
)
async def author_finance_overview(
    user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await finance_service.author_overview(db, user, days=days)
