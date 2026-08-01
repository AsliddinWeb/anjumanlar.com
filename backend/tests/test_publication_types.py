"""Publication type CRUD + RBAC checks."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, UserRole, UserStatus

PW = "Hunter22!"


async def _bake_user(
    db_session: AsyncSession,
    email: str,
    role: UserRole = UserRole.reader,
) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="PubType Tester",
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _admin_token(api_client: AsyncClient, db_session: AsyncSession) -> str:
    admin = await _bake_user(db_session, "admin-pubtypes@example.com", role=UserRole.admin)
    body = (
        await api_client.post(
            "/api/v1/auth/login",
            json={"email": admin.email, "password": PW},
        )
    ).json()
    return body["access_token"]


# ---------- public list + lookup ----------


@pytest.mark.asyncio
async def test_list_publication_types_seeded(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/publication-types")
    assert resp.status_code == 200
    body = resp.json()
    slugs = {item["slug"] for item in body["items"]}
    # The migration seeds these six — assert they survived (dev/test DB
    # is shared, so don't assert an exact total).
    assert {
        "textbook",
        "monograph",
        "study-guide",
        "lecture-notes",
        "dictionary",
        "conference-proceedings",
    }.issubset(slugs)


@pytest.mark.asyncio
async def test_get_by_slug_404_for_missing(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/publication-types/does-not-exist")
    assert resp.status_code == 404


# ---------- admin CRUD + RBAC ----------


@pytest.mark.asyncio
async def test_create_publication_type_requires_admin(
    api_client: AsyncClient, db_session: AsyncSession
):
    reader = await _bake_user(db_session, "reader-pubtypes@example.com")
    token = (
        await api_client.post("/api/v1/auth/login", json={"email": reader.email, "password": PW})
    ).json()["access_token"]
    resp = await api_client.post(
        "/api/v1/publication-types",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": "x", "name": {"uz": "X"}},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_then_get_by_slug(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    resp = await api_client.post(
        "/api/v1/publication-types",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slug": "thesis-test",
            "name": {"uz": "Tezis", "ru": "Тезисы", "en": "Thesis"},
            "sort_order": 5,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "thesis-test"

    fetched = await api_client.get("/api/v1/publication-types/thesis-test")
    assert fetched.status_code == 200
    assert fetched.json()["sort_order"] == 5


@pytest.mark.asyncio
async def test_create_rejects_duplicate_slug(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"slug": "dup-pubtype-test", "name": {"uz": "Dup"}}

    first = await api_client.post("/api/v1/publication-types", headers=headers, json=payload)
    assert first.status_code == 201

    second = await api_client.post("/api/v1/publication-types", headers=headers, json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_patch_publication_type_updates_field(
    api_client: AsyncClient, db_session: AsyncSession
):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    created = (
        await api_client.post(
            "/api/v1/publication-types",
            headers=headers,
            json={"slug": "patch-pubtype-test", "name": {"uz": "Patch"}},
        )
    ).json()

    patched = await api_client.patch(
        f"/api/v1/publication-types/{created['id']}",
        headers=headers,
        json={"sort_order": 9, "is_active": False},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["sort_order"] == 9
    assert body["is_active"] is False


@pytest.mark.asyncio
async def test_delete_publication_type(api_client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    created = (
        await api_client.post(
            "/api/v1/publication-types",
            headers=headers,
            json={"slug": "delete-pubtype-test", "name": {"uz": "Del"}},
        )
    ).json()

    resp = await api_client.delete(
        f"/api/v1/publication-types/{created['id']}", headers=headers
    )
    assert resp.status_code == 204

    miss = await api_client.get("/api/v1/publication-types/delete-pubtype-test")
    assert miss.status_code == 404


@pytest.mark.asyncio
async def test_deleting_publication_type_nulls_book_reference(
    api_client: AsyncClient, db_session: AsyncSession
):
    """ON DELETE SET NULL — deleting a type shouldn't cascade-delete books."""
    from app.models import AuthorProfile, Book, BookLanguage, BookStatus, PublicationType

    token = await _admin_token(api_client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    ptype = PublicationType(slug="orphan-test", name={"uz": "Orphan"})
    db_session.add(ptype)
    await db_session.flush()

    author_user = await _bake_user(
        db_session, "pubtype-book-author@example.com", role=UserRole.author
    )
    profile = AuthorProfile(
        user_id=author_user.id, slug="pubtype-book-author", display_name="A"
    )
    db_session.add(profile)
    await db_session.flush()

    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug="pubtype-orphan-book",
        title={"uz": "T"},
        language=BookLanguage.uz,
        price=10_000,
        status=BookStatus.draft,
        publication_type_id=ptype.id,
    )
    db_session.add(book)
    await db_session.flush()
    book_id = book.id
    ptype_id = ptype.id

    resp = await api_client.delete(f"/api/v1/publication-types/{ptype_id}", headers=headers)
    assert resp.status_code == 204

    await db_session.refresh(book)
    assert book.id == book_id
    assert book.publication_type_id is None
