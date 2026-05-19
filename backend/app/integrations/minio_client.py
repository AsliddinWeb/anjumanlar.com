"""Thin wrapper over the MinIO SDK.

Buckets are created once on first boot by the ``minio-init`` service in
``docker-compose.yml`` — we don't try to create them here.

This module exposes a single module-level ``minio_client`` (sync) — the
SDK itself is not async, so wrapping in asyncio.to_thread() at the
call-site is the recommended pattern when used from FastAPI.
"""

from __future__ import annotations

import contextlib
from io import BytesIO

from minio import Minio

from app.config import settings


def _build_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
    )


minio_client: Minio = _build_client()


def put_bytes(
    bucket: str,
    object_key: str,
    data: bytes,
    content_type: str,
) -> str:
    """Upload ``data`` to ``bucket/object_key`` and return the publicly-served URL."""
    minio_client.put_object(
        bucket_name=bucket,
        object_name=object_key,
        data=BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return f"{settings.MINIO_PUBLIC_ENDPOINT}/{bucket}/{object_key}"


def remove_object(bucket: str, object_key: str) -> None:
    """Idempotent delete — missing objects are silently ignored."""
    with contextlib.suppress(Exception):  # pragma: no cover — best-effort cleanup
        minio_client.remove_object(bucket, object_key)
