"""ORM smoke tests for User / RefreshToken / AuthToken.

Verifies columns map correctly, defaults fire, and relationships cascade.
Each test runs inside a rollback fixture so the real DB stays clean.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_opaque_token, hash_opaque_token, hash_password
from app.models import AuthToken, AuthTokenPurpose, RefreshToken, User, UserRole, UserStatus


async def _make_user(db: AsyncSession, email: str = "test@example.com") -> User:
    user = User(
        email=email,
        password_hash=hash_password("Hunter2!"),
        full_name="Test User",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_user_defaults_applied(db_session: AsyncSession):
    user = await _make_user(db_session)
    assert user.id is not None
    assert user.role == UserRole.reader
    assert user.status == UserStatus.pending
    assert user.email_verified is False
    assert user.phone_verified is False
    assert user.preferred_locale == "uz"
    assert user.preferences == {}
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_email_is_case_insensitive_unique(db_session: AsyncSession):
    """citext index must reject differing case as a duplicate."""
    from sqlalchemy.exc import IntegrityError

    await _make_user(db_session, "Foo@Example.com")
    db_session.add(
        User(
            email="foo@EXAMPLE.com",
            password_hash=hash_password("Hunter2!"),
            full_name="Dup",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_refresh_token_persists_and_links_to_user(db_session: AsyncSession):
    user = await _make_user(db_session, "ref@example.com")
    token_plain = generate_opaque_token()
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_opaque_token(token_plain),
        expires_at=datetime.now(UTC) + timedelta(days=7),
        user_agent="pytest",
        ip_address="127.0.0.1",
    )
    db_session.add(rt)
    await db_session.flush()
    await db_session.refresh(rt)

    assert rt.id is not None
    assert rt.revoked_at is None
    assert rt.token_hash != token_plain  # plaintext never stored

    # Reverse relationship loads the token from the user.
    fetched = await db_session.execute(select(User).where(User.id == user.id))
    fetched_user = fetched.scalar_one()
    await db_session.refresh(fetched_user, ["refresh_tokens"])
    assert len(fetched_user.refresh_tokens) == 1


@pytest.mark.asyncio
async def test_refresh_token_cascade_delete_when_user_removed(db_session: AsyncSession):
    user = await _make_user(db_session, "cascade@example.com")
    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_opaque_token(generate_opaque_token()),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
    )
    await db_session.flush()

    await db_session.delete(user)
    await db_session.flush()

    remaining = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    assert remaining.scalars().first() is None


@pytest.mark.asyncio
async def test_auth_token_with_purpose(db_session: AsyncSession):
    user = await _make_user(db_session, "verify@example.com")
    for purpose in AuthTokenPurpose:
        db_session.add(
            AuthToken(
                user_id=user.id,
                token_hash=hash_opaque_token(generate_opaque_token()),
                purpose=purpose,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    await db_session.flush()

    found = await db_session.execute(select(AuthToken).where(AuthToken.user_id == user.id))
    tokens = list(found.scalars())
    assert len(tokens) == 2
    assert {t.purpose for t in tokens} == set(AuthTokenPurpose)
    assert all(t.used_at is None for t in tokens)
