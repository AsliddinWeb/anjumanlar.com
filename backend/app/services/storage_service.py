"""Higher-level storage helpers.

For now we only handle avatar upload. Phase 2 will add book PDF, cover image,
and demo handling here too.
"""

from __future__ import annotations

import io
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.core.exceptions import ValidationError
from app.integrations.minio_client import put_bytes

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
