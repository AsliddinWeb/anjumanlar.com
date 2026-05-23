"""Blog post lifecycle coverage — service state machine + HTTP RBAC."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import BlogPost, BlogPostStatus, User, UserRole, UserStatus
from app.schemas.blog import BlogPostCreate
from app.services import blog_service

PW = "Hunter22!"


async def _make_user(
    db: AsyncSession, email: str, role: UserRole = UserRole.reader
) -> User:
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


async def _token(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- service ----------


@pytest.mark.asyncio
async def test_create_post_starts_as_draft(db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-author@example.com", UserRole.admin)
    post = await blog_service.create(
        db_session,
        admin,
        BlogPostCreate(slug="hello", title={"uz": "Salom"}),
    )
    assert post.status == BlogPostStatus.draft
    assert post.created_by == admin.id


@pytest.mark.asyncio
async def test_create_rejects_empty_title(db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-empty@example.com", UserRole.admin)
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await blog_service.create(
            db_session,
            admin,
            BlogPostCreate(slug="empty", title={"uz": "  "}),
        )


@pytest.mark.asyncio
async def test_publish_sets_timestamp(db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-publish@example.com", UserRole.admin)
    post = await blog_service.create(
        db_session, admin, BlogPostCreate(slug="pub", title={"uz": "Pub"})
    )
    assert post.published_at is None

    await blog_service.publish(db_session, post.id)
    await db_session.refresh(post)
    assert post.status == BlogPostStatus.published
    assert post.published_at is not None


@pytest.mark.asyncio
async def test_duplicate_slug_returns_conflict(db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-dup@example.com", UserRole.admin)
    await blog_service.create(
        db_session, admin, BlogPostCreate(slug="dup", title={"uz": "A"})
    )
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await blog_service.create(
            db_session, admin, BlogPostCreate(slug="dup", title={"uz": "B"})
        )


@pytest.mark.asyncio
async def test_unpublish_blocks_non_published(db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-unpub@example.com", UserRole.admin)
    post = await blog_service.create(
        db_session, admin, BlogPostCreate(slug="unpub", title={"uz": "A"})
    )
    from app.core.exceptions import ConflictError

    with pytest.raises(ConflictError):
        await blog_service.unpublish(db_session, post.id)


# ---------- HTTP ----------


@pytest.mark.asyncio
async def test_public_list_hides_drafts(api_client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(db_session, "blog-http-admin@example.com", UserRole.admin)
    draft = await blog_service.create(
        db_session, admin, BlogPostCreate(slug="draft-only", title={"uz": "D"})
    )
    pub = await blog_service.create(
        db_session, admin, BlogPostCreate(slug="published-one", title={"uz": "P"})
    )
    await blog_service.publish(db_session, pub.id)
    await db_session.commit()

    resp = await api_client.get("/api/v1/blog")
    assert resp.status_code == 200
    slugs = {p["slug"] for p in resp.json()["items"]}
    assert "published-one" in slugs
    assert "draft-only" not in slugs


@pytest.mark.asyncio
async def test_public_detail_only_for_published(
    api_client: AsyncClient, db_session: AsyncSession
):
    admin = await _make_user(db_session, "blog-detail-admin@example.com", UserRole.admin)
    draft = await blog_service.create(
        db_session, admin, BlogPostCreate(slug="secret-draft", title={"uz": "S"})
    )
    await db_session.commit()

    resp = await api_client.get(f"/api/v1/blog/{draft.slug}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_create_requires_admin(
    api_client: AsyncClient, db_session: AsyncSession
):
    reader = await _make_user(db_session, "blog-reader@example.com")
    await db_session.commit()
    token = await _token(api_client, reader.email)
    resp = await api_client.post(
        "/api/v1/admin/blog",
        headers=_h(token),
        json={"slug": "nope", "title": {"uz": "Reader's post"}},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_publish_via_http(
    api_client: AsyncClient, db_session: AsyncSession
):
    admin = await _make_user(db_session, "blog-publish-admin@example.com", UserRole.admin)
    await db_session.commit()
    token = await _token(api_client, admin.email)

    created = await api_client.post(
        "/api/v1/admin/blog",
        headers=_h(token),
        json={"slug": "publish-via-http", "title": {"uz": "Via HTTP"}},
    )
    assert created.status_code == 201
    pid = created.json()["id"]

    pub = await api_client.post(
        f"/api/v1/admin/blog/{pid}/publish", headers=_h(token)
    )
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"
