"""Service for the singleton ``site_settings`` row."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SiteSettings


async def get(db: AsyncSession) -> SiteSettings:
    """Return the singleton row. The migration seeds it; if a deployment
    skipped that step (e.g. dev DB created via metadata.create_all) we
    create the row on first access so callers can always assume one row
    exists.
    """
    row = (await db.execute(select(SiteSettings))).scalar_one_or_none()
    if row is None:
        row = SiteSettings(theme_name="classic")
        db.add(row)
        await db.flush()
    return row


async def update_theme(db: AsyncSession, theme_name: str) -> SiteSettings:
    row = await get(db)
    row.theme_name = theme_name
    await db.flush()
    return row


async def update_ornament(db: AsyncSession, ornament_name: str) -> SiteSettings:
    row = await get(db)
    row.ornament_name = ornament_name
    await db.flush()
    return row


async def update_animations(db: AsyncSession, enabled: bool) -> SiteSettings:
    row = await get(db)
    row.animations_enabled = enabled
    await db.flush()
    return row
