"""Admin dashboard KPI snapshot.

A single ``GET`` returns the entire payload — the frontend treats the
response as opaque JSON since the shape is rendered card-by-card and
adding a new card on the backend doesn't require a frontend type bump.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import User
from app.services import stats_service

router = APIRouter(prefix="/admin", tags=["admin-stats"])
public_router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/stats",
    summary="Aggregated KPIs for the admin dashboard",
)
async def admin_stats(
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await stats_service.snapshot(db)


@public_router.get(
    "/public",
    summary="Public-safe counters for the homepage hero strip",
)
async def public_stats(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    return await stats_service.public_snapshot(db)
