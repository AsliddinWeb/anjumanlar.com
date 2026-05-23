"""Pydantic schemas for the admin audit-log feed."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import AuditAction


class AuditLogPublic(BaseModel):
    """Admin-only — exposes user_id + IP, which is too much for end users."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    action: AuditAction
    ip_address: str | None = None
    user_agent: str | None = None
    meta: dict[str, Any]
    created_at: datetime

    @field_validator("ip_address", mode="before")
    @classmethod
    def _ip_to_str(cls, v):
        # Postgres' INET column round-trips as an ipaddress.IPv4Address/
        # IPv6Address; pydantic expects a plain string here.
        if v is None:
            return None
        return str(v)


class AuditLogList(BaseModel):
    items: list[AuditLogPublic]
    total: int
    page: int
    page_size: int
