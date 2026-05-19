"""Tests for app.core.security primitives."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_opaque_token,
    verify_password,
)

# ---------- Passwords ----------


def test_password_hash_is_not_plaintext():
    h = hash_password("Hunter2!")
    assert h != "Hunter2!"
    assert h.startswith("$2b$") or h.startswith("$2a$")


def test_password_verify_roundtrip():
    h = hash_password("Hunter2!")
    assert verify_password("Hunter2!", h) is True
    assert verify_password("wrong", h) is False


def test_password_hash_is_salted():
    """Same password → different hashes (bcrypt random salt)."""
    assert hash_password("same") != hash_password("same")


# ---------- JWT access tokens ----------


def test_access_token_roundtrip():
    token = create_access_token("user-id-123")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-id-123"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_carries_extra_claims():
    token = create_access_token("user-id-1", extra_claims={"role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["role"] == "admin"


def test_access_token_rejects_garbage():
    assert decode_access_token("not-a-token") is None
    assert decode_access_token("a.b.c") is None


def test_access_token_rejects_expired():
    token = create_access_token("user-id-1", expires_in=timedelta(seconds=-1))
    assert decode_access_token(token) is None


def test_access_token_rejects_non_access_type():
    """If we ever hand a token to decode_access_token whose 'type' is not 'access',
    it must be rejected — protects /auth/refresh's payload from being used as an
    access bearer."""
    # Forge a token with type=refresh using the same machinery.
    from jose import jwt

    from app.config import settings

    bad = jwt.encode(
        {"sub": "u", "type": "refresh", "exp": 9_999_999_999},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert decode_access_token(bad) is None


# ---------- Opaque tokens ----------


def test_opaque_token_is_url_safe_and_unique():
    a = generate_opaque_token()
    b = generate_opaque_token()
    assert a != b
    # 32 bytes URL-safe ≈ 43 chars
    assert len(a) >= 40
    # URL-safe alphabet
    import string

    allowed = set(string.ascii_letters + string.digits + "-_")
    assert set(a).issubset(allowed)


def test_opaque_token_hash_is_deterministic():
    t = "abc-def-123"
    assert hash_opaque_token(t) == hash_opaque_token(t)


def test_opaque_token_hash_differs_from_plain():
    t = "abc-def-123"
    assert hash_opaque_token(t) != t


def test_opaque_token_verify_roundtrip():
    t = generate_opaque_token()
    h = hash_opaque_token(t)
    assert verify_opaque_token(t, h) is True
    assert verify_opaque_token("tampered", h) is False


@pytest.mark.parametrize("size", [16, 24, 32, 48])
def test_opaque_token_size_param(size: int):
    t = generate_opaque_token(size)
    # URL-safe-base64 of N bytes = ceil(4N/3), minus padding (which `secrets`
    # omits). For our four sizes that's >= N+ a few.
    assert len(t) > size
