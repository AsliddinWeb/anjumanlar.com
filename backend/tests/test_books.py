"""Book CRUD, status machine, admin moderation, RBAC.

Each test creates its own author + reader users so the rollback fixture
gives clean slate every time.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import AuthorProfile, User, UserRole, UserStatus

PW = "Hunter22!"


async def _make_user(db: AsyncSession, email: str, role: UserRole = UserRole.reader) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Tester",
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


async def _make_author(db: AsyncSession, email: str) -> tuple[User, AuthorProfile]:
    user = await _make_user(db, email, role=UserRole.author)
    profile = AuthorProfile(
        user_id=user.id,
        slug=email.split("@")[0] + "-slug",
        display_name="Author " + email.split("@")[0],
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return user, profile


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _book_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": {"uz": "Tarix asoslari", "en": "Foundations of History"},
        "description": {"uz": "Qisqacha"},
        "language": "uz",
        "price": 50000,
    }
    payload.update(overrides)
    return payload


# ---------- Create ----------


@pytest.mark.asyncio
async def test_create_book_requires_author_role(api_client: AsyncClient, db_session: AsyncSession):
    reader = await _make_user(db_session, "reader-books@example.com")
    token = await _token(api_client, reader.email)
    resp = await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_book_requires_author_profile(
    api_client: AsyncClient, db_session: AsyncSession
):
    """User has ``author`` role but no profile yet → 403 with no_author_profile."""
    user = await _make_user(db_session, "no-profile@example.com", role=UserRole.author)
    token = await _token(api_client, user.email)
    resp = await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    assert resp.status_code == 403
    assert resp.json()["error"]["details"]["code"] == "no_author_profile"


@pytest.mark.asyncio
async def test_create_book_succeeds_for_author(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "create-book@example.com")
    token = await _token(api_client, user.email)
    resp = await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "draft"
    assert body["title"]["uz"] == "Tarix asoslari"
    assert body["slug"].startswith("tarix-asoslari")


@pytest.mark.asyncio
async def test_create_book_rejects_empty_title(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "empty-title@example.com")
    token = await _token(api_client, user.email)
    resp = await api_client.post(
        "/api/v1/books",
        headers=_h(token),
        json=_book_payload(title={"uz": "", "en": ""}),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_unique_slug_collision(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "dupe-slug@example.com")
    token = await _token(api_client, user.email)
    payload = _book_payload(title={"uz": "Bir Xil Sarlavha"})
    r1 = await api_client.post("/api/v1/books", headers=_h(token), json=payload)
    r2 = await api_client.post("/api/v1/books", headers=_h(token), json=payload)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["slug"] != r2.json()["slug"]


# ---------- Update + status transitions ----------


@pytest.mark.asyncio
async def test_author_can_edit_own_draft(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "edit@example.com")
    token = await _token(api_client, user.email)
    created = (
        await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    ).json()
    patch = await api_client.patch(
        f"/api/v1/books/{created['id']}",
        headers=_h(token),
        json={"price": 99000, "publisher": "Universitet"},
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["price"] == 99000
    assert body["publisher"] == "Universitet"


@pytest.mark.asyncio
async def test_other_author_cannot_edit_book(api_client: AsyncClient, db_session: AsyncSession):
    owner, _ = await _make_author(db_session, "owner@example.com")
    other, _ = await _make_author(db_session, "stranger@example.com")
    owner_token = await _token(api_client, owner.email)
    other_token = await _token(api_client, other.email)
    created = (
        await api_client.post("/api/v1/books", headers=_h(owner_token), json=_book_payload())
    ).json()
    resp = await api_client.patch(
        f"/api/v1/books/{created['id']}",
        headers=_h(other_token),
        json={"price": 1},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_submit_book_moves_to_pending(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "submit@example.com")
    token = await _token(api_client, user.email)
    created = (
        await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    ).json()
    resp = await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_cannot_edit_after_submit(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "frozen@example.com")
    token = await _token(api_client, user.email)
    created = (
        await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(token))
    resp = await api_client.patch(
        f"/api/v1/books/{created['id']}", headers=_h(token), json={"price": 1}
    )
    assert resp.status_code == 409


# ---------- Admin moderation ----------


async def _admin_token(api_client: AsyncClient, db: AsyncSession) -> str:
    admin = await _make_user(db, "admin-books@example.com", role=UserRole.admin)
    return await _token(api_client, admin.email)


@pytest.mark.asyncio
async def test_approve_moves_pending_to_approved_and_publishes(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "approve@example.com")
    author_t = await _token(api_client, user.email)
    admin_t = await _admin_token(api_client, db_session)

    created = (
        await api_client.post("/api/v1/books", headers=_h(author_t), json=_book_payload())
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(author_t))
    resp = await api_client.post(
        f"/api/v1/books/admin/{created['id']}/approve", headers=_h(admin_t)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["published_at"] is not None

    # Public catalogue now shows it.
    listed = await api_client.get("/api/v1/books")
    slugs = [it["slug"] for it in listed.json()["items"]]
    assert body["slug"] in slugs


@pytest.mark.asyncio
async def test_reject_records_reason(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "reject@example.com")
    author_t = await _token(api_client, user.email)
    admin_t = await _admin_token(api_client, db_session)
    created = (
        await api_client.post("/api/v1/books", headers=_h(author_t), json=_book_payload())
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(author_t))
    resp = await api_client.post(
        f"/api/v1/books/admin/{created['id']}/reject",
        headers=_h(admin_t),
        json={"reason": "Plagiat aniqlandi"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "Plagiat aniqlandi"


@pytest.mark.asyncio
async def test_rejected_book_can_be_edited_and_resubmitted(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "loop@example.com")
    author_t = await _token(api_client, user.email)
    admin_t = await _admin_token(api_client, db_session)
    created = (
        await api_client.post("/api/v1/books", headers=_h(author_t), json=_book_payload())
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(author_t))
    await api_client.post(
        f"/api/v1/books/admin/{created['id']}/reject",
        headers=_h(admin_t),
        json={"reason": "Tuzating"},
    )
    patched = await api_client.patch(
        f"/api/v1/books/{created['id']}",
        headers=_h(author_t),
        json={"description": {"uz": "Tuzatildi"}},
    )
    assert patched.status_code == 200
    resubmit = await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(author_t))
    assert resubmit.status_code == 200
    assert resubmit.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_moderation_queue_only_pending(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "q@example.com")
    author_t = await _token(api_client, user.email)
    admin_t = await _admin_token(api_client, db_session)

    # One draft (NOT in queue), one pending (in queue)
    draft = (
        await api_client.post(
            "/api/v1/books", headers=_h(author_t), json=_book_payload(title={"uz": "Draft kitob"})
        )
    ).json()
    pending = (
        await api_client.post(
            "/api/v1/books", headers=_h(author_t), json=_book_payload(title={"uz": "Pending kitob"})
        )
    ).json()
    await api_client.post(f"/api/v1/books/{pending['id']}/submit", headers=_h(author_t))

    resp = await api_client.get("/api/v1/books/admin/moderation", headers=_h(admin_t))
    assert resp.status_code == 200
    slugs = [it["slug"] for it in resp.json()["items"]]
    assert pending["slug"] in slugs
    assert draft["slug"] not in slugs


@pytest.mark.asyncio
async def test_admin_endpoints_require_admin(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "noadmin@example.com")
    token = await _token(api_client, user.email)
    resp = await api_client.get("/api/v1/books/admin/moderation", headers=_h(token))
    assert resp.status_code == 403


# ---------- Public listing filters ----------


@pytest.mark.asyncio
async def test_public_list_only_shows_approved(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "pubfilter@example.com")
    token = await _token(api_client, user.email)
    draft = (
        await api_client.post(
            "/api/v1/books",
            headers=_h(token),
            json=_book_payload(title={"uz": "Hidden draft only"}),
        )
    ).json()
    listed = await api_client.get("/api/v1/books", params={"search": "Hidden draft only"})
    slugs = [it["slug"] for it in listed.json()["items"]]
    assert draft["slug"] not in slugs


@pytest.mark.asyncio
async def test_get_public_by_slug_404_for_draft(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "slugdraft@example.com")
    token = await _token(api_client, user.email)
    draft = (await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())).json()
    resp = await api_client.get(f"/api/v1/books/{draft['slug']}")
    assert resp.status_code == 404


# ---------- /books/me ----------


@pytest.mark.asyncio
async def test_my_books_lists_all_statuses(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "myown@example.com")
    token = await _token(api_client, user.email)
    await api_client.post("/api/v1/books", headers=_h(token), json=_book_payload())
    resp = await api_client.get("/api/v1/books/me", headers=_h(token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
