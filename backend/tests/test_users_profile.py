"""Profile read/patch, avatar upload, soft delete, RBAC aliases.

Avatar upload hits the real MinIO container in the dev stack — the bucket
is provisioned by ``minio-init`` on first compose up, so no setup is needed
here.
"""

from __future__ import annotations

import io

import httpx
import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.models import User, UserRole, UserStatus

PW = "Hunter22!"


def _make_jpeg_bytes(size: tuple[int, int] = (300, 400), color: str = "red") -> bytes:
    """Generate a small JPEG payload to feed multipart/form-data."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="JPEG")
    return buf.getvalue()


# ---------- fixtures ----------


async def _bake_user(
    db_session: AsyncSession,
    *,
    email: str,
    role: UserRole = UserRole.reader,
    status: UserStatus = UserStatus.active,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Test User",
        role=role,
        status=status,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _login(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PW},
        )
    ).json()
    return body["access_token"]


# ---------- GET /users/me ----------


@pytest.mark.asyncio
async def test_get_me_requires_bearer(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_profile(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="getme@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


# ---------- PATCH /users/me ----------


@pytest.mark.asyncio
async def test_patch_me_updates_only_supplied_fields(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, email="patch@example.com")
    token = await _login(api_client, user.email)

    resp = await api_client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "  Renamed  ", "preferences": {"theme": "dark"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Renamed"  # stripped
    # preferred_locale stayed at the default since we didn't supply it.
    assert body["preferred_locale"] == user.preferred_locale


@pytest.mark.asyncio
async def test_patch_me_rejects_invalid_locale(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="locale@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"preferred_locale": "fr"},
    )
    assert resp.status_code == 422


# ---------- POST /users/me/avatar ----------


@pytest.mark.asyncio
async def test_upload_avatar_resizes_and_stores_url(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, email="avatar@example.com")
    token = await _login(api_client, user.email)

    jpeg = _make_jpeg_bytes()
    resp = await api_client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("me.jpg", jpeg, "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    url = resp.json()["avatar_url"]
    assert url is not None
    assert str(user.id) in url

    # Confirm the public bucket actually serves the object. Tests run inside
    # the backend container so we hit the *internal* MinIO endpoint, not the
    # host-mapped 8302 port the URL returned to the browser would use.
    object_url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_AVATARS}/{user.id}.jpg"
    async with httpx.AsyncClient(timeout=5) as c:
        head = await c.head(object_url)
    assert head.status_code == 200
    # Resized version is way smaller than the original 300x400.
    assert int(head.headers["content-length"]) < len(jpeg)


@pytest.mark.asyncio
async def test_upload_avatar_rejects_non_image(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="badmime@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("hack.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_avatar_rejects_corrupted_image_with_image_mime(
    api_client: AsyncClient, db_session: AsyncSession
):
    """MIME says image/jpeg but the bytes aren't really an image — Pillow
    must reject."""
    user = await _bake_user(db_session, email="corrupt@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fake.jpg", b"not really a jpeg", "image/jpeg")},
    )
    assert resp.status_code == 422


# ---------- DELETE /users/me ----------


@pytest.mark.asyncio
async def test_delete_me_soft_deletes_and_frees_email(
    api_client: AsyncClient, db_session: AsyncSession
):
    user = await _bake_user(db_session, email="bye@example.com")
    token = await _login(api_client, user.email)

    resp = await api_client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    await db_session.refresh(user)
    assert user.status == UserStatus.deleted
    assert user.deleted_at is not None
    assert user.email != "bye@example.com"  # anonymised

    # Original email is free again — registration with it should succeed.
    re = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "bye@example.com", "password": PW, "full_name": "Reborn"},
    )
    assert re.status_code == 201


# ---------- RBAC ----------


@pytest.mark.asyncio
async def test_admin_ping_403_for_reader(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="reader-rbac@example.com")
    token = await _login(api_client, user.email)
    resp = await api_client.get(
        "/api/v1/users/admin/ping", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_ping_403_for_author(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="author-rbac@example.com", role=UserRole.author)
    token = await _login(api_client, user.email)
    resp = await api_client.get(
        "/api/v1/users/admin/ping", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_ping_200_for_admin(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="admin-rbac@example.com", role=UserRole.admin)
    token = await _login(api_client, user.email)
    resp = await api_client.get(
        "/api/v1/users/admin/ping", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "hello admin"


@pytest.mark.asyncio
async def test_admin_ping_200_for_superadmin(api_client: AsyncClient, db_session: AsyncSession):
    user = await _bake_user(db_session, email="super-rbac@example.com", role=UserRole.superadmin)
    token = await _login(api_client, user.email)
    resp = await api_client.get(
        "/api/v1/users/admin/ping", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "hello superadmin"


# ---------- create_superadmin CLI ----------
#
# Tested manually via `docker compose exec backend python -m app.scripts.create_superadmin`
# rather than pytest: the script opens its own session and commits, which
# deadlocks against the rollback-fixture's outer transaction (uncommitted
# duplicate email blocks the script's INSERT and the script's session blocks
# the rollback).
