"""Pydantic request/response schemas for the /auth/* endpoints."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models import UserRole, UserStatus

# Password policy mirrors docs/03-backend/03-authentication.md §"Parol siyosati":
# 8+ chars, at least one uppercase letter, one lowercase letter, one digit.
_PW_UPPER = re.compile(r"[A-Z]")
_PW_LOWER = re.compile(r"[a-z]")
_PW_DIGIT = re.compile(r"\d")


def _password_policy(v: str) -> str:
    if not _PW_UPPER.search(v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not _PW_LOWER.search(v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not _PW_DIGIT.search(v):
        raise ValueError("Password must contain at least one digit")
    return v


# Reusable password type — registers as a string in OpenAPI but enforces
# length + complexity on input.
PasswordStr = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(_password_policy),
]


class UserRegister(BaseModel):
    email: EmailStr
    password: PasswordStr
    full_name: str = Field(..., min_length=1, max_length=255)
    preferred_locale: Literal["uz", "ru", "en"] = "uz"

    @field_validator("full_name")
    @classmethod
    def _full_name_strip(cls, v: str) -> str:
        return v.strip()


class UserPublic(BaseModel):
    """Safe-to-return shape — never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    email_verified: bool
    avatar_url: str | None = None
    preferred_locale: str
    created_at: datetime


class UserList(BaseModel):
    items: list[UserPublic]
    total: int
    page: int
    page_size: int


class AdminUserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserStatusUpdate(BaseModel):
    status: UserStatus


class AdminUserCreate(BaseModel):
    """Admin payload for POST /admin/users — create a user from the panel.

    Skips the email-verification dance: created accounts land active and
    email-verified so the admin doesn't have to chase a confirmation link.
    """

    email: EmailStr
    password: PasswordStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.reader
    status: UserStatus = UserStatus.active
    preferred_locale: Literal["uz", "ru", "en"] = "uz"

    @field_validator("full_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class AdminUserUpdate(BaseModel):
    """Admin PATCH payload for /admin/users/{id} — every field optional."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    status: UserStatus | None = None
    password: PasswordStr | None = None

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class EmailVerifyRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=128)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


# ----- Login / tokens -----


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenPair(BaseModel):
    """Issued by /login and /refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expires


class LoginResponse(TokenPair):
    """Login also embeds the user object so the frontend can avoid an extra
    /me call right after authenticating."""

    user: UserPublic


class RefreshRequest(BaseModel):
    """Refresh token is read from cookie when this body is omitted."""

    refresh_token: str | None = None


class SessionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    expires_at: datetime
    user_agent: str | None = None
    ip_address: str | None = None
    is_current: bool = False


class SessionList(BaseModel):
    items: list[SessionInfo]
    total: int


# ----- Password reset / change -----


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=128)
    new_password: PasswordStr


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: PasswordStr


# ----- Profile -----


class UserUpdate(BaseModel):
    """PATCH-style payload: every field is optional; absent keys are untouched."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    preferred_locale: Literal["uz", "ru", "en"] | None = None
    preferences: dict | None = None

    @field_validator("full_name")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return v.strip() if v else v
