"""Category CRUD + tree assembly + RBAC checks."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import Category, User, UserRole, UserStatus

PW = "Hunter22!"


async def _bake_user(
    db_session: AsyncSession,
    email: str,
    role: UserRole = UserRole.reader,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Cat Tester",
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _admin_token(api_client: AsyncClient, db_session: AsyncSession) -> str:
    admin = await _bake_user(db_session, "admin-cats@example.com", role=UserRole.admin)
    body = (
        await api_client.post(
            "/api/v1/auth/login",
            json={"email": admin.email, "password": PW},
        )
    ).json()
    return body["access_token"]


# ---------- public list + tree ----------


@pytest.mark.asyncio
async def test_list_categories_empty(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/categories")
    assert resp.status_code == 200
    body = resp.json()
    # DB may already have seed data; just assert the envelope is well-formed.
    assert "items" in body and "total" in body


@pytest.mark.asyncio
async def test_tree_assembly(api_client: AsyncClient, db_session: AsyncSession):
    root = Category(slug="science-test", name={"uz": "Fan", "en": "Science"})
    db_session.add(root)
    await db_session.flush()
    child = Category(
        slug="physics-test",
        name={"uz": "Fizika", "en": "Physics"},
        parent_id=root.id,
    )
    db_session.add(child)
    await db_session.flush()

    resp = await api_client.get("/api/v1/categories/tree")
    assert resp.status_code == 200
    nodes = resp.json()
    # Find our test root by slug.
    matching_root = next((n for n in nodes if n["slug"] == "science-test"), None)
    assert matching_root is not None
    child_slugs = [c["slug"] for c in matching_root["children"]]
    assert "physics-test" in child_slugs


# ---------- admin CRUD + RBAC ----------


@pytest.mark.asyncio
async def test_create_category_requires_admin(api_client: AsyncClient, db_session: AsyncSession):
    reader = await _bake_user(db_session, "reader-cats@example.com")
    token = (
        await api_client.post("/api/v1/auth/login", json={"email": reader.email, "password": PW})
    ).json()["access_token"]
    resp = await api_client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": "x", "name": {"uz": "X"}},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_then_get_by_slug(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    resp = await api_client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slug": "history-test",
            "name": {"uz": "Tarix", "ru": "История", "en": "History"},
            "sort_order": 5,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "history-test"

    # Public lookup
    fetched = await api_client.get("/api/v1/categories/history-test")
    assert fetched.status_code == 200
    assert fetched.json()["sort_order"] == 5


@pytest.mark.asyncio
async def test_create_rejects_duplicate_slug(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"slug": "dup-test", "name": {"uz": "Dup"}}

    first = await api_client.post("/api/v1/categories", headers=headers, json=payload)
    assert first.status_code == 201

    second = await api_client.post("/api/v1/categories", headers=headers, json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_patch_category_updates_field(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    created = (
        await api_client.post(
            "/api/v1/categories",
            headers=headers,
            json={"slug": "patch-cat-test", "name": {"uz": "Patch"}},
        )
    ).json()

    patched = await api_client.patch(
        f"/api/v1/categories/{created['id']}",
        headers=headers,
        json={"icon": "📚", "sort_order": 9},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["icon"] == "📚"
    assert body["sort_order"] == 9


@pytest.mark.asyncio
async def test_patch_rejects_self_parent(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    created = (
        await api_client.post(
            "/api/v1/categories",
            headers=headers,
            json={"slug": "self-parent-test", "name": {"uz": "Self"}},
        )
    ).json()

    resp = await api_client.patch(
        f"/api/v1/categories/{created['id']}",
        headers=headers,
        json={"parent_id": created["id"]},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["details"]["code"] == "self_parent"


@pytest.mark.asyncio
async def test_delete_category(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    created = (
        await api_client.post(
            "/api/v1/categories",
            headers=headers,
            json={"slug": "delete-cat-test", "name": {"uz": "Del"}},
        )
    ).json()

    resp = await api_client.delete(f"/api/v1/categories/{created['id']}", headers=headers)
    assert resp.status_code == 204

    miss = await api_client.get("/api/v1/categories/delete-cat-test")
    assert miss.status_code == 404
