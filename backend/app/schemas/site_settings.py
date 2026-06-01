"""Schemas for /settings + /admin/settings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsPublic(BaseModel):
    """Public-safe shape — what the frontend reads on every page load
    to set the active theme. Add new public toggles here."""

    model_config = ConfigDict(from_attributes=True)

    theme_name: str


class SiteSettingsUpdate(BaseModel):
    """Admin PATCH payload — every field optional."""

    theme_name: str | None = Field(default=None, min_length=1, max_length=64)
