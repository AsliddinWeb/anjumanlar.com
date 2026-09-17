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
    author_uploads_enabled: bool
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    telegram_url: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    youtube_url: str | None = None


class SiteSettingsUpdate(BaseModel):
    """Admin PATCH payload — every field optional."""

    theme_name: str | None = Field(default=None, min_length=1, max_length=64)
    ornament_name: str | None = Field(default=None, min_length=1, max_length=64)
    animations_enabled: bool | None = None
    author_uploads_enabled: bool | None = None
    contact_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=255)
    telegram_url: str | None = Field(default=None, max_length=255)
    instagram_url: str | None = Field(default=None, max_length=255)
    facebook_url: str | None = Field(default=None, max_length=255)
    youtube_url: str | None = Field(default=None, max_length=255)
