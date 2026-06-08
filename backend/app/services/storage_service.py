"""Higher-level storage helpers.

Avatars (Phase 1.6), book covers (Phase 2.3) and original book PDFs
(Phase 2.3) all flow through here. Demo PDF generation + watermarking
land in Phase 2.4 as Celery tasks but reuse the same MinIO client.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import settings
from app.core.exceptions import ValidationError
from app.integrations.minio_client import put_bytes

# ---------------------------------------------------------------------------
# Avatars
# ---------------------------------------------------------------------------

ALLOWED_AVATAR_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
AVATAR_MAX_DIMENSION = 256
AVATAR_JPEG_QUALITY = 85


def _validate_and_normalize_avatar(raw: bytes, content_type: str) -> bytes:
    """Sanity-check + transcode to a fixed 256x256 JPEG.

    We re-encode rather than trusting the upload: that way we never serve
    an attacker-controlled image (e.g. a polyglot SVG with embedded JS).
    """
    if content_type.lower() not in ALLOWED_AVATAR_MIME:
        raise ValidationError(f"Unsupported avatar MIME type: {content_type}")

    if len(raw) > settings.MAX_AVATAR_FILE_MB * 1024 * 1024:
        raise ValidationError(f"Avatar exceeds the {settings.MAX_AVATAR_FILE_MB} MB limit")

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()  # forces decode + raises on truncated input
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("File is not a valid image") from exc

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((AVATAR_MAX_DIMENSION, AVATAR_MAX_DIMENSION))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=AVATAR_JPEG_QUALITY, optimize=True)
    return out.getvalue()


def upload_avatar(user_id: UUID, raw: bytes, content_type: str) -> str:
    """Validate, normalise, push to MinIO. Returns the public URL.

    Uploads always overwrite the existing object — there's only ever one
    avatar per user, keyed by ``<user_id>.jpg``.
    """
    normalised = _validate_and_normalize_avatar(raw, content_type)
    return put_bytes(
        settings.MINIO_BUCKET_AVATARS,
        f"{user_id}.jpg",
        normalised,
        "image/jpeg",
    )


# ---------------------------------------------------------------------------
# Book covers
# ---------------------------------------------------------------------------

ALLOWED_COVER_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
COVER_TARGET_WIDTH = 800
COVER_TARGET_HEIGHT = 1200
COVER_JPEG_QUALITY = 88


def _validate_and_normalize_cover(raw: bytes, content_type: str) -> bytes:
    """Re-encode the upload to an 800x1200-ish JPEG. We don't *force* the
    aspect ratio — Pillow's ``thumbnail`` preserves it — but we cap both
    dimensions so the cover never exceeds 800x1200."""
    if content_type.lower() not in ALLOWED_COVER_MIME:
        raise ValidationError(
            f"Unsupported cover MIME type: {content_type}",
            details={"code": "cover_bad_mime"},
        )

    if len(raw) > settings.MAX_COVER_FILE_MB * 1024 * 1024:
        raise ValidationError(
            f"Cover exceeds the {settings.MAX_COVER_FILE_MB} MB limit",
            details={"code": "cover_too_large"},
        )

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(
            "File is not a valid image", details={"code": "cover_bad_image"}
        ) from exc

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((COVER_TARGET_WIDTH, COVER_TARGET_HEIGHT))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=COVER_JPEG_QUALITY, optimize=True)
    return out.getvalue()


def upload_book_cover(book_id: UUID, raw: bytes, content_type: str) -> str:
    """Validate, resize, push to the public ``covers`` bucket. Overwrites
    any previous cover for the same book."""
    normalised = _validate_and_normalize_cover(raw, content_type)
    return put_bytes(
        settings.MINIO_BUCKET_COVERS,
        f"{book_id}.jpg",
        normalised,
        "image/jpeg",
    )


# ---------------------------------------------------------------------------
# Book files (the original PDF)
# ---------------------------------------------------------------------------

ALLOWED_BOOK_MIME = {"application/pdf"}


@dataclass(frozen=True)
class BookFileUpload:
    """What the service layer needs back after a book PDF is stored."""

    url: str
    pages_count: int
    file_size_mb: float


def _validate_pdf(raw: bytes, content_type: str) -> int:
    """Return the page count if ``raw`` is a sound PDF, else raise."""
    if content_type.lower() not in ALLOWED_BOOK_MIME:
        raise ValidationError(
            f"Unsupported file type: {content_type}",
            details={"code": "book_bad_mime"},
        )

    if len(raw) > settings.MAX_BOOK_FILE_MB * 1024 * 1024:
        raise ValidationError(
            f"File exceeds the {settings.MAX_BOOK_FILE_MB} MB limit",
            details={"code": "book_too_large"},
        )

    try:
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValidationError(
                "Encrypted PDFs are not supported",
                details={"code": "book_encrypted"},
            )
        pages = len(reader.pages)
    except PdfReadError as exc:
        raise ValidationError(
            "File is not a valid PDF",
            details={"code": "book_bad_pdf"},
        ) from exc

    if pages < 1:
        raise ValidationError(
            "PDF has no pages",
            details={"code": "book_empty"},
        )
    return pages


# ---------------------------------------------------------------------------
# Review-request files
# ---------------------------------------------------------------------------

REVIEW_MANUSCRIPT_MIME = {"application/pdf"}
REVIEW_MAX_MB = 100


def upload_review_manuscript(
    request_id: UUID, raw: bytes, content_type: str, filename: str | None = None
) -> tuple[str, str | None]:
    """Push a peer-review manuscript PDF into the books bucket.

    Returns (url, original_filename). We piggyback on the existing
    ``books`` bucket since both store PDFs that need to be private +
    served via presigned URLs.
    """
    if content_type.lower() not in REVIEW_MANUSCRIPT_MIME:
        raise ValidationError("Manuscript must be a PDF")
    if len(raw) > REVIEW_MAX_MB * 1024 * 1024:
        raise ValidationError(f"Manuscript exceeds the {REVIEW_MAX_MB} MB limit")
    # Light PDF sanity-check so we don't store junk.
    try:
        PdfReader(io.BytesIO(raw))
    except PdfReadError as exc:
        raise ValidationError("File is not a valid PDF") from exc

    url = put_bytes(
        settings.MINIO_BUCKET_BOOKS,
        f"review-manuscripts/{request_id}.pdf",
        raw,
        "application/pdf",
    )
    safe_name = filename.strip() if filename else None
    if safe_name and len(safe_name) > 255:
        safe_name = safe_name[:255]
    return url, safe_name


def upload_review_response_file(
    request_id: UUID, raw: bytes, content_type: str
) -> str:
    """Author's supporting file alongside the textual review.

    PDF only, capped at REVIEW_MAX_MB. Stored under a separate prefix
    so the manuscript and the response don't collide.
    """
    if content_type.lower() not in REVIEW_MANUSCRIPT_MIME:
        raise ValidationError("Review file must be a PDF")
    if len(raw) > REVIEW_MAX_MB * 1024 * 1024:
        raise ValidationError(f"Review file exceeds the {REVIEW_MAX_MB} MB limit")
    try:
        PdfReader(io.BytesIO(raw))
    except PdfReadError as exc:
        raise ValidationError("File is not a valid PDF") from exc

    return put_bytes(
        settings.MINIO_BUCKET_BOOKS,
        f"review-responses/{request_id}.pdf",
        raw,
        "application/pdf",
    )


def upload_book_demo(book_id: UUID, raw: bytes, content_type: str) -> str:
    """Drop a manually-supplied demo PDF into the public ``demos`` bucket."""
    _validate_pdf(raw, content_type)
    return put_bytes(
        settings.MINIO_BUCKET_DEMOS,
        f"{book_id}.pdf",
        raw,
        "application/pdf",
    )


def upload_book_file(book_id: UUID, raw: bytes, content_type: str) -> BookFileUpload:
    """Validate the PDF, drop the original into the *private* ``books`` bucket.

    The demo PDF + per-buyer watermarked copy are generated later (Phase 2.4
    + Phase 4) and stored in their own buckets — this function only deals
    with the canonical source file.
    """
    pages_count = _validate_pdf(raw, content_type)
    url = put_bytes(
        settings.MINIO_BUCKET_BOOKS,
        f"{book_id}.pdf",
        raw,
        "application/pdf",
    )
    size_mb = round(len(raw) / (1024 * 1024), 2)
    return BookFileUpload(url=url, pages_count=pages_count, file_size_mb=size_mb)
