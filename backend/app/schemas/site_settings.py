"""Schemas for /settings + /admin/settings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsPublic(BaseModel):
    """Public-safe shape — what the frontend reads on every page load
    to set the active theme + ornament + animation state."""

    model_config = ConfigDict(from_attributes=True)

    theme_name: str
    ornament_name: str
    animations_enabled: bool


class SiteSettingsUpdate(BaseModel):
    """Admin PATCH payload — every field optional."""

    theme_name: str | None = Field(default=None, min_length=1, max_length=64)
    ornament_name: str | None = Field(default=None, min_length=1, max_length=64)
    animations_enabled: bool | None = None
