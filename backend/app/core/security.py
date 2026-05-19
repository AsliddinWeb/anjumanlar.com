"""Cryptographic primitives used across the auth stack.

Three distinct token families live here:

- **Access tokens**: short-lived JWTs (default 30 min) carrying the user id
  in `sub`. Stateless — verified by signature only.
- **Refresh tokens**: opaque high-entropy strings handed to the client.
  Their SHA-256 hash is stored in the `refresh_tokens` table so they can be
  revoked. The bare string is only ever sent over TLS to the client.
- **Single-purpose tokens** (email verification, password reset): identical
  shape to refresh tokens — opaque + hashed — but stored in `auth_tokens`
  with a `purpose` enum and a `used_at` column so each can fire exactly once.

Passwords use bcrypt (12 rounds) via passlib.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ----- Passwords -----

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ----- JWT access tokens -----

TokenType = Literal["access"]


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_in: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_in or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode + verify signature/expiry. Returns None on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


# ----- Opaque tokens (refresh + email/reset) -----
#
# Opaque tokens are URL-safe random strings. The plaintext goes to the client,
# the hash goes to the DB. We use HMAC-SHA256 (not bcrypt) because:
#   1. The input already has 256 bits of entropy — no brute-force risk.
#   2. Auth requests hit this hot path frequently; bcrypt would be wasteful.
#   3. We need constant-time equality, which HMAC's verify gives us.


def generate_opaque_token(n_bytes: int = 32) -> str:
    """Return a URL-safe random token. 32 bytes ≈ 43 chars, 256-bit strength."""
    return secrets.token_urlsafe(n_bytes)


def hash_opaque_token(token: str) -> str:
    """HMAC-SHA256 over JWT_SECRET_KEY. Stored verbatim in the DB."""
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_opaque_token(token: str, stored_hash: str) -> bool:
    """Constant-time check of an opaque token against its stored hash."""
    return hmac.compare_digest(hash_opaque_token(token), stored_hash)
