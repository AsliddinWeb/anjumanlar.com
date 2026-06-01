"""Site-wide settings endpoints.

- ``GET /settings``         — public; what the frontend reads on
                              boot to apply the active theme.
- ``PATCH /admin/settings`` — admin write path.

Two routers because the read endpoint must be reachable without a
session (SSR pre-fetch on every page) while the write endpoint sits
under the admin guard.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas.site_settings import SiteSettingsPublic, SiteSettingsUpdate
from app.services import site_settings_service

public_router = APIRouter(prefix="/settings", tags=["settings"])
admin_router = APIRouter(prefix="/admin/settings", tags=["settings"])


@public_router.get(
    "",
    response_model=SiteSettingsPublic,
    summary="Site-wide settings exposed to the frontend (theme, etc.)",
)
async def read_settings(db: AsyncSession = Depends(get_db)) -> SiteSettingsPublic:
    row = await site_settings_service.get(db)
    return SiteSettingsPublic.model_validate(row)


@admin_router.get(
    "",
    response_model=SiteSettingsPublic,
    summary="Same payload as /settings — convenience for the admin panel",
)
async def admin_read_settings(
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> SiteSettingsPublic:
    row = await site_settings_service.get(db)
    return SiteSettingsPublic.model_validate(row)


@admin_router.patch(
    "",
    response_model=SiteSettingsPublic,
    summary="Update site settings (admin+)",
)
async def admin_update_settings(
    data: SiteSettingsUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> SiteSettingsPublic:
    if data.theme_name is not None:
        await site_settings_service.update_theme(db, data.theme_name)
    row = await site_settings_service.get(db)
    await db.commit()
    return SiteSettingsPublic.model_validate(row)
