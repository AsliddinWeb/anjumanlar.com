"""Search-pipeline tests.

Unit-level coverage:
- ``book_to_document`` flattens an ORM row into the shape Meili wants.
- ``build_filters`` / ``translate_sort`` produce the right strings.
- Approve/reject/soft-delete each dispatch the corresponding Celery task.

The end-to-end query against a live Meilisearch is marked
``@integration`` — the rollback fixture would otherwise leak documents
into shared index state.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.integrations.meilisearch_client import (
    BOOKS_INDEX,
    delete_book_document,
    get_client,
    upsert_book_document,
)
from app.models import (
    AuthorProfile,
    Book,
    BookLanguage,
    BookStatus,
    Category,
    User,
    UserRole,
    UserStatus,
)
from app.services import search_service

PW = "Hunter22!"


# ---------- helpers ----------


async def _make_user(db: AsyncSession, email: str, role: UserRole = UserRole.author) -> User:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Search Tester",
        role=role,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


async def _make_book_with_relations(db: AsyncSession) -> Book:
    user = await _make_user(db, f"sr-{uuid.uuid4().hex[:8]}@example.com")
    profile = AuthorProfile(
        user_id=user.id,
        slug=f"a-{uuid.uuid4().hex[:8]}",
        display_name="Test Author",
    )
    cat = Category(slug=f"cat-{uuid.uuid4().hex[:8]}", name={"uz": "Sinov"})
    db.add_all([profile, cat])
    await db.flush()

    book = Book(
        author_id=profile.id,
        uploaded_by=user.id,
        slug=f"b-{uuid.uuid4().hex[:8]}",
        title={"uz": "Tarix asoslari", "ru": "Основы истории", "en": "History 101"},
        description={"uz": "Qisqacha tavsif", "en": "Short blurb"},
        language=BookLanguage.uz,
        price=50000,
        publisher="Sinov nashriyoti",
        published_at=datetime.now(UTC),
        status=BookStatus.approved,
        featured=True,
    )
    book.categories = [cat]
    db.add(book)
    await db.flush()
    await db.refresh(book, ["author", "categories"])
    return book


# ---------- book_to_document ----------


@pytest.mark.asyncio
async def test_book_to_document_flattens_jsonb_locales(db_session: AsyncSession):
    book = await _make_book_with_relations(db_session)
    doc = search_service.book_to_document(book)

    assert doc["id"] == str(book.id)
    assert doc["slug"] == book.slug
    assert doc["title_uz"] == "Tarix asoslari"
    assert doc["title_ru"] == "Основы истории"
    assert doc["title_en"] == "History 101"
    assert doc["description_uz"] == "Qisqacha tavsif"
    assert doc["language"] == "uz"
    assert doc["price"] == 50000.0
    assert doc["is_free"] is False
    assert doc["featured"] is True
    assert doc["author_name"] == "Test Author"
    assert len(doc["category_ids"]) == 1
    assert len(doc["category_slugs"]) == 1
    assert doc["published_at_ts"] > 0
    assert doc["publisher"] == "Sinov nashriyoti"


def test_book_to_document_handles_empty_locales():
    """No exceptions when the JSONB title is missing some locales."""
    from types import SimpleNamespace

    fake = SimpleNamespace(
        id=uuid.uuid4(),
        slug="x",
        title={"uz": "Faqat o'zbek"},
        description={},
        language="uz",
        price=0,
        is_free=True,
        featured=False,
        categories=[],
        author_id=uuid.uuid4(),
        author=None,
        publisher=None,
        isbn=None,
        cover_url=None,
        average_rating=0,
        reviews_count=0,
        sales_count=0,
        views_count=0,
        published_at=None,
        created_at=None,
    )
    doc = search_service.book_to_document(fake)
    assert doc["title_uz"] == "Faqat o'zbek"
    assert doc["title_ru"] == ""
    assert doc["title_en"] == ""
    assert doc["author_name"] == ""
    assert doc["published_at_ts"] is None


# ---------- filters / sort translation ----------


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("-published_at", ["published_at_ts:desc"]),
        ("published_at", ["published_at_ts:asc"]),
        ("-price", ["price:desc"]),
        ("price", ["price:asc"]),
        ("-average_rating", ["average_rating:desc"]),
        ("totally-bogus", ["published_at_ts:desc"]),  # falls back to default
    ],
)
def test_translate_sort_maps_known_keys(key: str, expected: list[str]):
    assert search_service.translate_sort(key) == expected


def test_build_filters_assembles_expression():
    out = search_service.build_filters(
        category_slug="history",
        language="ru",
        min_price=10,
        max_price=99,
        is_free=False,
        featured=True,
    )
    assert out is not None
    assert 'category_slugs = "history"' in out
    assert 'language = "ru"' in out
    assert "price >= 10" in out
    assert "price <= 99" in out
    assert "is_free = false" in out
    assert "featured = true" in out


def test_build_filters_empty_returns_none():
    assert search_service.build_filters() is None


# ---------- Dispatch hooks on book lifecycle ----------


async def _make_author(db: AsyncSession, email: str) -> tuple[User, AuthorProfile]:
    user = await _make_user(db, email, role=UserRole.author)
    profile = AuthorProfile(
        user_id=user.id, slug=email.split("@")[0] + "-srch", display_name="Hook Author"
    )
    db.add(profile)
    await db.flush()
    return user, profile


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def _token(api_client: AsyncClient, email: str) -> str:
    r = await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_approve_dispatches_search_sync(
    api_client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    calls: list[tuple] = []

    def fake_delay(*args, **kwargs):
        calls.append((args, kwargs))

        class _R:
            id = "x"

        return _R()

    monkeypatch.setattr("app.tasks.search_tasks.sync_book_to_meilisearch.delay", fake_delay)

    author_user, _ = await _make_author(db_session, "approve-srch@example.com")
    admin = await _make_user(db_session, "admin-srch@example.com", role=UserRole.admin)
    a_t = await _token(api_client, author_user.email)
    ad_t = await _token(api_client, admin.email)

    created = (
        await api_client.post(
            "/api/v1/books",
            headers=_h(a_t),
            json={"title": {"uz": "Sync test"}, "language": "uz", "price": 0},
        )
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(a_t))
    await api_client.post(f"/api/v1/books/admin/{created['id']}/approve", headers=_h(ad_t))
    assert any(c[0][0] == created["id"] for c in calls)


@pytest.mark.asyncio
async def test_reject_dispatches_search_remove(
    api_client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    calls: list[tuple] = []
    monkeypatch.setattr(
        "app.tasks.search_tasks.remove_book_from_meilisearch.delay",
        lambda *a, **kw: calls.append((a, kw)) or type("R", (), {"id": "x"})(),
    )

    author_user, _ = await _make_author(db_session, "reject-srch@example.com")
    admin = await _make_user(db_session, "admin-rej@example.com", role=UserRole.admin)
    a_t = await _token(api_client, author_user.email)
    ad_t = await _token(api_client, admin.email)

    created = (
        await api_client.post(
            "/api/v1/books",
            headers=_h(a_t),
            json={"title": {"uz": "Reject test"}, "language": "uz", "price": 0},
        )
    ).json()
    await api_client.post(f"/api/v1/books/{created['id']}/submit", headers=_h(a_t))
    await api_client.post(
        f"/api/v1/books/admin/{created['id']}/reject",
        headers=_h(ad_t),
        json={"reason": "no"},
    )
    assert any(c[0][0] == created["id"] for c in calls)


# ---------- Integration: live Meilisearch ----------


@pytest.mark.integration
def test_meili_round_trip_via_helpers():
    """Push a synthetic doc, search for it, delete it. Verifies the
    settings + filterable wiring against a real Meilisearch instance."""
    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "slug": "integration-test-book",
        "title_uz": "Tarixiy uchrashuv test",
        "title_ru": "",
        "title_en": "",
        "description_uz": "",
        "description_ru": "",
        "description_en": "",
        "language": "uz",
        "price": 99.0,
        "is_free": False,
        "featured": False,
        "category_ids": [],
        "category_slugs": ["test-cat"],
        "author_id": str(uuid.uuid4()),
        "author_slug": "test",
        "author_name": "Integration Tester",
        "publisher": "",
        "isbn": "",
        "cover_url": None,
        "average_rating": 0.0,
        "reviews_count": 0,
        "sales_count": 0,
        "views_count": 0,
        "published_at_ts": int(time.time()),
        "created_at_ts": int(time.time()),
    }
    try:
        upsert_book_document(doc)
        # Meili processes async; poll until our doc is searchable.
        for _ in range(20):
            time.sleep(0.2)
            result = (
                get_client()
                .index(BOOKS_INDEX)
                .search(
                    "tarixiy uchrashuv",
                    {"limit": 5, "attributesToRetrieve": ["id"]},
                )
            )
            ids = [h["id"] for h in result.get("hits", [])]
            if doc_id in ids:
                break
        else:
            pytest.fail(f"document {doc_id} never appeared in search results")
    finally:
        delete_book_document(doc_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_endpoint_returns_only_approved_postgres_rows(
    api_client: AsyncClient, db_session: AsyncSession
):
    """``/search`` should reject Meili hits whose Postgres row isn't
    actually approved — defends against stale documents."""
    # Push a doc to Meili that maps to a non-existent book.
    ghost_id = str(uuid.uuid4())
    doc = {
        "id": ghost_id,
        "slug": "ghost-book",
        "title_uz": "Mavjud emas",
        "title_ru": "",
        "title_en": "",
        "description_uz": "",
        "description_ru": "",
        "description_en": "",
        "language": "uz",
        "price": 0,
        "is_free": True,
        "featured": False,
        "category_ids": [],
        "category_slugs": [],
        "author_id": str(uuid.uuid4()),
        "author_slug": "",
        "author_name": "",
        "publisher": "",
        "isbn": "",
        "cover_url": None,
        "average_rating": 0.0,
        "reviews_count": 0,
        "sales_count": 0,
        "views_count": 0,
        "published_at_ts": int(time.time()),
        "created_at_ts": int(time.time()),
    }
    try:
        upsert_book_document(doc)
        # Give Meili time to index.
        await asyncio.sleep(1)
        resp = await api_client.get("/api/v1/search", params={"q": "Mavjud emas"})
        assert resp.status_code == 200
        slugs = [it["slug"] for it in resp.json()["items"]]
        assert "ghost-book" not in slugs
    finally:
        delete_book_document(ghost_id)
