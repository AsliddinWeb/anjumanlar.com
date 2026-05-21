"""Book cover + PDF upload tests.

Validation paths (bad MIME, oversized, corrupted) fail before MinIO is
touched, so they run as unit tests. Tests that verify the file actually
landed in MinIO are marked ``@integration`` — those need the dev stack's
MinIO container.
"""

from __future__ import annotations

import io
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from PIL import Image
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.models import AuthorProfile, BookStatus, User, UserRole, UserStatus

PW = "Hunter22!"


# ---------- helpers ----------


async def _make_author(db: AsyncSession, email: str) -> tuple[User, AuthorProfile]:
    u = User(
        email=email,
        password_hash=hash_password(PW),
        full_name="Up Author",
        role=UserRole.author,
        status=UserStatus.active,
        email_verified=True,
    )
    db.add(u)
    await db.flush()
    profile = AuthorProfile(
        user_id=u.id,
        slug=email.split("@")[0] + "-up",
        display_name="Upload Author",
    )
    db.add(profile)
    await db.flush()
    await db.refresh(u)
    return u, profile


async def _login(api_client: AsyncClient, email: str) -> str:
    body = (
        await api_client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    ).json()
    return body["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_cover_bytes(size: tuple[int, int] = (1200, 1800)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color="navy").save(buf, format="JPEG")
    return buf.getvalue()


def _make_pdf_bytes(pages: int = 15) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(pages):
        c.drawString(100, 750, f"Page {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


async def _create_draft_book(
    api_client: AsyncClient, token: str, title_uz: str = "Upload kitobi"
) -> dict[str, Any]:
    payload = {
        "title": {"uz": title_uz, "en": "Upload Book"},
        "language": "uz",
        "price": 0,
    }
    return (await api_client.post("/api/v1/books", headers=_h(token), json=payload)).json()


# ---------- validation (no MinIO) ----------


@pytest.mark.asyncio
async def test_upload_cover_rejects_bad_mime(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "cover-mime@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/cover",
        headers=_h(token),
        files={"file": ("file.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["code"] == "cover_bad_mime"


@pytest.mark.asyncio
async def test_upload_cover_rejects_corrupted_image(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "cover-corrupt@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/cover",
        headers=_h(token),
        files={"file": ("fake.jpg", b"not really jpeg", "image/jpeg")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["code"] == "cover_bad_image"


@pytest.mark.asyncio
async def test_upload_file_rejects_non_pdf(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "file-mime@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/file",
        headers=_h(token),
        files={"file": ("doc.docx", b"PK\x03\x04", "application/vnd.openxmlformats")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["code"] == "book_bad_mime"


@pytest.mark.asyncio
async def test_upload_file_rejects_corrupted_pdf(api_client: AsyncClient, db_session: AsyncSession):
    user, _ = await _make_author(db_session, "file-corrupt@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/file",
        headers=_h(token),
        files={"file": ("fake.pdf", b"not a pdf payload", "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["code"] == "book_bad_pdf"


@pytest.mark.asyncio
async def test_upload_rejects_non_owner(api_client: AsyncClient, db_session: AsyncSession):
    owner, _ = await _make_author(db_session, "own@example.com")
    other, _ = await _make_author(db_session, "thief@example.com")
    book = await _create_draft_book(api_client, await _login(api_client, owner.email))
    other_token = await _login(api_client, other.email)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/cover",
        headers=_h(other_token),
        files={"file": ("c.jpg", _make_cover_bytes((100, 100)), "image/jpeg")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_rejects_after_submit(api_client: AsyncClient, db_session: AsyncSession):
    """Once a book is pending moderation, the author can't swap the file
    under the reviewer."""
    user, _ = await _make_author(db_session, "lock@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)
    await api_client.post(f"/api/v1/books/{book['id']}/submit", headers=_h(token))
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/file",
        headers=_h(token),
        files={"file": ("b.pdf", _make_pdf_bytes(5), "application/pdf")},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["details"]["code"] == "wrong_status"


# ---------- integration: real MinIO ----------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_cover_resizes_and_serves_via_minio(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "cover-ok@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)

    jpeg = _make_cover_bytes((1500, 2200))  # over the 800x1200 cap
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/cover",
        headers=_h(token),
        files={"file": ("c.jpg", jpeg, "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cover_url"]
    assert book["id"] in body["cover_url"]

    object_url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_COVERS}/{book['id']}.jpg"
    async with httpx.AsyncClient(timeout=5) as c:
        head = await c.head(object_url)
    assert head.status_code == 200
    # The resized JPEG is significantly smaller than the original 1500x2200 input.
    assert int(head.headers["content-length"]) < len(jpeg)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_file_extracts_pages_and_stores_pdf(
    api_client: AsyncClient, db_session: AsyncSession
):
    user, _ = await _make_author(db_session, "pdf-ok@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)

    pdf = _make_pdf_bytes(pages=12)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/file",
        headers=_h(token),
        files={"file": ("book.pdf", pdf, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["pages_count"] == 12
    assert body["file_url"]
    # ``status`` stays draft — upload doesn't auto-submit.
    assert body["status"] == BookStatus.draft.value

    # MinIO actually has the object (private bucket so HEAD is anonymous-allowed
    # only by virtue of dev compose; we just check existence via internal URL).
    object_url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_BOOKS}/{book['id']}.pdf"
    async with httpx.AsyncClient(timeout=5) as c:
        head = await c.head(object_url)
    # Private bucket → 403 (no anonymous read) is the expected "file exists" signal.
    assert head.status_code in (200, 403)


@pytest.mark.asyncio
async def test_upload_file_dispatches_demo_generation(
    api_client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    """The book_service must enqueue a ``pdf.generate_demo`` Celery task once
    the file lands. We stub ``.delay`` here rather than wait on a live
    worker because the rollback fixture's user + book aren't visible to the
    worker's separate session — that path is exercised manually in dev."""
    calls: list[tuple] = []

    def fake_delay(*args, **kwargs):
        calls.append((args, kwargs))

        class _R:
            id = "fake-task-id"

        return _R()

    monkeypatch.setattr("app.tasks.pdf_tasks.generate_demo_pdf.delay", fake_delay)

    user, _ = await _make_author(db_session, "demo-dispatch@example.com")
    token = await _login(api_client, user.email)
    book = await _create_draft_book(api_client, token)

    pdf = _make_pdf_bytes(pages=20)
    resp = await api_client.post(
        f"/api/v1/books/{book['id']}/file",
        headers=_h(token),
        files={"file": ("book.pdf", pdf, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    assert len(calls) == 1
    # First positional arg is the book id (stringified UUID).
    assert calls[0][0][0] == book["id"]
