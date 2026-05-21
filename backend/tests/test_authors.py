"""Author profile lifecycle: become-author, /me, list, public lookup."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import AuthorProfile, User, UserRole, UserStatus

PW = "Hunter22!"


async def _bake_user(
    db_session: AsyncSession,
    email: str,
    role: UserRole = UserRole.reader,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Sample User",
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _login(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


# ---------- become-author ----------


@pytest.mark.asyncio
async def test_become_author_upgrades_role_and_creates_profile(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, "newauthor@example.com")
    token = await _login(api_client, user.email)

    resp = await api_client.post(
        "/api/v1/authors/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Aziz Karimov",
            "bio": {"uz": "Tarix fanlari doktori", "en": "PhD in History"},
            "academic_title": "PhD",
            "institution": "Universitet 1",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["display_name"] == "Aziz Karimov"
    assert body["slug"].startswith("aziz-karimov")
    assert body["bio"]["uz"] == "Tarix fanlari doktori"

    await db_session.refresh(user)
    assert user.role == UserRole.author


@pytest.mark.asyncio
async def test_become_author_rejects_second_call(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, "dup@example.com")
    token = await _login(api_client, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    first = await api_client.post(
        "/api/v1/authors/me", headers=headers, json={"display_name": "Once"}
    )
    assert first.status_code == 201

    second = await api_client.post(
        "/api/v1/authors/me", headers=headers, json={"display_name": "Twice"}
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_become_author_generates_unique_slug(
    api_client: AsyncClient, db_session: AsyncSession
):
    """Two users sharing a display_name should get different slugs."""
    u1 = await _bake_user(db_session, "a@example.com")
    u2 = await _bake_user(db_session, "b@example.com")
    t1 = await _login(api_client, u1.email)
    t2 = await _login(api_client, u2.email)

    r1 = await api_client.post(
        "/api/v1/authors/me",
        headers={"Authorization": f"Bearer {t1}"},
        json={"display_name": "Same Name"},
    )
    r2 = await api_client.post(
        "/api/v1/authors/me",
        headers={"Authorization": f"Bearer {t2}"},
        json={"display_name": "Same Name"},
    )
    assert r1.status_code == 201 and r2.status_code == 201
    slug1 = r1.json()["slug"]
    slug2 = r2.json()["slug"]
    assert slug1 != slug2
    assert slug1 == "same-name"
    assert slug2.startswith("same-name-")


# ---------- /authors/me ----------


@pytest.mark.asyncio
async def test_get_me_returns_404_when_no_profile(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, "nope@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.get("/api/v1/authors/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_me_updates_only_supplied_fields(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, "patch@example.com")
    token = await _login(api_client, user.email)
    h = {"Authorization": f"Bearer {token}"}

    await api_client.post("/api/v1/authors/me", headers=h, json={"display_name": "Old Name"})
    resp = await api_client.patch(
        "/api/v1/authors/me",
        headers=h,
        json={"academic_title": "Professor", "bio": {"uz": "Yangi bio"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["academic_title"] == "Professor"
    assert body["bio"]["uz"] == "Yangi bio"
    assert body["display_name"] == "Old Name"  # unchanged


# ---------- public list + slug lookup ----------


@pytest.mark.asyncio
async def test_public_list_only_includes_active_users(
    api_client: AsyncClient, db_session: AsyncSession
):
    visible = await _bake_user(db_session, "vis@example.com")
    blocked = await _bake_user(db_session, "blk@example.com")
    db_session.add_all(
        [
            AuthorProfile(user_id=visible.id, slug="visible-one", display_name="Visible One"),
            AuthorProfile(user_id=blocked.id, slug="blocked-one", display_name="Blocked One"),
        ]
    )
    blocked.status = UserStatus.blocked
    await db_session.flush()

    resp = await api_client.get("/api/v1/authors", params={"search": "blocked"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp2 = await api_client.get("/api/v1/authors", params={"search": "visible"})
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 1


@pytest.mark.asyncio
async def test_public_slug_lookup(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, "slug@example.com")
    db_session.add(AuthorProfile(user_id=user.id, slug="slug-author", display_name="Slug Author"))
    await db_session.flush()

    resp = await api_client.get("/api/v1/authors/slug-author")
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == "slug-author"
    # Private fields must not leak into the public payload.
    assert "commission_rate" not in body
    assert "bank_details" not in body
    assert "pending_balance" not in body


@pytest.mark.asyncio
async def test_public_slug_lookup_404(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/authors/no-such-author")
    assert resp.status_code == 404
