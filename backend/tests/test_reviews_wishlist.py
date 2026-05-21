"""Reviews + wishlist coverage.

Reviews exercise:
- create / dedup / edit-resets-to-pending / delete (own + admin)
- moderation queue + approve/reject
- rating aggregate maths on the book row

Wishlist exercise: add / dedup / list / remove.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import (
    AuthorProfile,
    Book,
    BookLanguage,
    BookStatus,
    User,
    UserRole,
    UserStatus,
)

PW = "Hunter22!"


# ---------- helpers ----------


async def _make_user(db: AsyncSession, email: str, role: UserRole = UserRole.reader) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name=email.split("@")[0],
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


async def _make_approved_book(db: AsyncSession, slug: str = "test-book") -> Book:
    author_user = await _make_user(db, f"author-{slug}@example.com", UserRole.author)
    profile = AuthorProfile(user_id=author_user.id, slug=f"prof-{slug}", display_name="Book Author")
    db.add(profile)
    await db.flush()
    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug=slug,
        title={"uz": "Sinov kitobi"},
        language=BookLanguage.uz,
        price=10000,
        status=BookStatus.approved,
        published_at=datetime.now(UTC),
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _admin_token(api_client: AsyncClient, db: AsyncSession) -> str:
    admin = await _make_user(db, "admin-reviews@example.com", role=UserRole.admin)
    return await _token(api_client, admin.email)


# ---------- reviews: create / dedup ----------


@pytest.mark.asyncio
async def test_create_review_requires_auth(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "anon-review")
    resp = await api_client.post(
        f"/api/v1/books/{book.id}/reviews",
        json={"rating": 5, "body": "Yaxshi"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_review_returns_pending_status(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "first-review")
    reader = await _make_user(db_session, "reader-r@example.com")
    token = await _token(api_client, reader.email)
    resp = await api_client.post(
        f"/api/v1/books/{book.id}/reviews",
        headers=_h(token),
        json={"rating": 4, "title": "OK", "body": "Yaxshi kitob"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["rating"] == 4
    assert body["body"] == "Yaxshi kitob"
    # ``status`` only appears on admin view; the public payload must NOT
    # leak the pending flag.
    assert "status" not in body


@pytest.mark.asyncio
async def test_duplicate_review_returns_409(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "dup-review")
    reader = await _make_user(db_session, "dup-r@example.com")
    token = await _token(api_client, reader.email)
    payload: dict[str, Any] = {"rating": 5, "body": "OK"}
    a = await api_client.post(f"/api/v1/books/{book.id}/reviews", headers=_h(token), json=payload)
    assert a.status_code == 201
    b = await api_client.post(f"/api/v1/books/{book.id}/reviews", headers=_h(token), json=payload)
    assert b.status_code == 409
    assert b.json()["error"]["details"]["code"] == "duplicate_review"


@pytest.mark.asyncio
async def test_create_review_validates_rating_range(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "rating-bad")
    reader = await _make_user(db_session, "rating-r@example.com")
    token = await _token(api_client, reader.email)
    for bad in (0, 6, -1, 10):
        resp = await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(token),
            json={"rating": bad, "body": "x"},
        )
        assert resp.status_code == 422


# ---------- public list excludes pending/rejected ----------


@pytest.mark.asyncio
async def test_public_list_only_shows_approved(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "list-test")
    reader = await _make_user(db_session, "list-r@example.com")
    token = await _token(api_client, reader.email)
    await api_client.post(
        f"/api/v1/books/{book.id}/reviews",
        headers=_h(token),
        json={"rating": 5, "body": "pending one"},
    )
    listed = await api_client.get(f"/api/v1/books/{book.id}/reviews")
    assert listed.status_code == 200
    assert listed.json()["total"] == 0  # nothing approved yet


# ---------- own edit + delete ----------


@pytest.mark.asyncio
async def test_owner_can_patch_and_review_returns_to_pending(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "patch-rev")
    reader = await _make_user(db_session, "patch-r@example.com")
    token = await _token(api_client, reader.email)
    admin_t = await _admin_token(api_client, db_session)

    created = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(token),
            json={"rating": 3, "body": "ok"},
        )
    ).json()
    # Admin approves so the next edit can demonstrate "back to pending"
    await api_client.post(
        f"/api/v1/admin/reviews/{created['id']}/approve",
        headers=_h(admin_t),
    )
    patch = await api_client.patch(
        f"/api/v1/reviews/{created['id']}",
        headers=_h(token),
        json={"rating": 5, "body": "yaxshilandi"},
    )
    assert patch.status_code == 200
    # The book's aggregate should drop back to 0 once the row leaves the
    # approved set.
    await db_session.refresh(book)
    assert book.reviews_count == 0
    assert float(book.average_rating) == 0.0


@pytest.mark.asyncio
async def test_other_user_cannot_patch_review(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "patch-other")
    owner = await _make_user(db_session, "owner-rev@example.com")
    intruder = await _make_user(db_session, "intruder-rev@example.com")
    owner_t = await _token(api_client, owner.email)
    intruder_t = await _token(api_client, intruder.email)
    created = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(owner_t),
            json={"rating": 5, "body": "yaxshi"},
        )
    ).json()
    resp = await api_client.patch(
        f"/api/v1/reviews/{created['id']}",
        headers=_h(intruder_t),
        json={"rating": 1},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_delete_review(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "del-rev")
    reader = await _make_user(db_session, "del-r@example.com")
    token = await _token(api_client, reader.email)
    created = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(token),
            json={"rating": 5, "body": "delete me"},
        )
    ).json()
    resp = await api_client.delete(f"/api/v1/reviews/{created['id']}", headers=_h(token))
    assert resp.status_code == 204


# ---------- admin moderation + rating aggregate ----------


@pytest.mark.asyncio
async def test_admin_approve_updates_book_aggregate(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "agg-test")
    reader = await _make_user(db_session, "agg-r@example.com")
    reader2 = await _make_user(db_session, "agg-r2@example.com")
    t1 = await _token(api_client, reader.email)
    t2 = await _token(api_client, reader2.email)
    admin_t = await _admin_token(api_client, db_session)

    r1 = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(t1),
            json={"rating": 4, "body": "ok"},
        )
    ).json()
    r2 = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(t2),
            json={"rating": 5, "body": "great"},
        )
    ).json()

    await api_client.post(f"/api/v1/admin/reviews/{r1['id']}/approve", headers=_h(admin_t))
    await api_client.post(f"/api/v1/admin/reviews/{r2['id']}/approve", headers=_h(admin_t))

    await db_session.refresh(book)
    assert book.reviews_count == 2
    assert float(book.average_rating) == pytest.approx(4.5)


@pytest.mark.asyncio
async def test_admin_reject_excludes_from_aggregate(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "rej-agg")
    reader = await _make_user(db_session, "rej-r@example.com")
    token = await _token(api_client, reader.email)
    admin_t = await _admin_token(api_client, db_session)

    created = (
        await api_client.post(
            f"/api/v1/books/{book.id}/reviews",
            headers=_h(token),
            json={"rating": 1, "body": "spam"},
        )
    ).json()
    await api_client.post(f"/api/v1/admin/reviews/{created['id']}/approve", headers=_h(admin_t))
    await db_session.refresh(book)
    assert book.reviews_count == 1

    await api_client.post(f"/api/v1/admin/reviews/{created['id']}/reject", headers=_h(admin_t))
    await db_session.refresh(book)
    assert book.reviews_count == 0
    assert float(book.average_rating) == 0.0


@pytest.mark.asyncio
async def test_moderation_endpoint_requires_admin(
    api_client: AsyncClient, db_session: AsyncSession
):
    reader = await _make_user(db_session, "rmod-reader@example.com")
    token = await _token(api_client, reader.email)
    resp = await api_client.get("/api/v1/admin/reviews", headers=_h(token))
    assert resp.status_code == 403


# ---------- wishlist ----------


@pytest.mark.asyncio
async def test_wishlist_add_list_remove_roundtrip(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "wl-roundtrip")
    reader = await _make_user(db_session, "wl-r@example.com")
    token = await _token(api_client, reader.email)

    add = await api_client.post(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert add.status_code == 201
    assert add.json()["book"]["slug"] == book.slug

    listed = await api_client.get("/api/v1/users/me/wishlist", headers=_h(token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    remove = await api_client.delete(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert remove.status_code == 204

    listed2 = await api_client.get("/api/v1/users/me/wishlist", headers=_h(token))
    assert listed2.json()["total"] == 0


@pytest.mark.asyncio
async def test_wishlist_add_twice_returns_409(api_client: AsyncClient, db_session: AsyncSession):
    book = await _make_approved_book(db_session, "wl-dup")
    reader = await _make_user(db_session, "wl-dup@example.com")
    token = await _token(api_client, reader.email)
    a = await api_client.post(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert a.status_code == 201
    b = await api_client.post(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert b.status_code == 409
    assert b.json()["error"]["details"]["code"] == "already_wished"


@pytest.mark.asyncio
async def test_wishlist_requires_auth(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/users/me/wishlist")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wishlist_404_for_unapproved_book(api_client: AsyncClient, db_session: AsyncSession):
    """Wishlists only reference approved + non-deleted books."""
    # Build a draft book that isn't visible publicly.
    author_user = await _make_user(db_session, "draft-author@example.com", UserRole.author)
    profile = AuthorProfile(user_id=author_user.id, slug="draft-prof", display_name="Drafter")
    db_session.add(profile)
    await db_session.flush()
    book = Book(
        author_id=profile.id,
        uploaded_by=author_user.id,
        slug="hidden-book",
        title={"uz": "Yashirin"},
        language=BookLanguage.uz,
        price=0,
        status=BookStatus.draft,
    )
    db_session.add(book)
    await db_session.flush()

    reader = await _make_user(db_session, "wl-404@example.com")
    token = await _token(api_client, reader.email)
    resp = await api_client.post(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_wishlist_remove_404_when_not_wished(
    api_client: AsyncClient, db_session: AsyncSession
):
    book = await _make_approved_book(db_session, "wl-rm-404")
    reader = await _make_user(db_session, "wl-rm-r@example.com")
    token = await _token(api_client, reader.email)
    resp = await api_client.delete(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_wishlist_persisted_correctly(api_client: AsyncClient, db_session: AsyncSession):
    """Sanity-check the DB row count matches the API view."""
    from app.models import Wishlist

    book = await _make_approved_book(db_session, "wl-db")
    reader = await _make_user(db_session, "wl-db@example.com")
    token = await _token(api_client, reader.email)
    await api_client.post(f"/api/v1/users/me/wishlist/{book.id}", headers=_h(token))
    rows = (
        (await db_session.execute(select(Wishlist).where(Wishlist.user_id == reader.id)))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].book_id == book.id
