"""Thin wrapper over the MinIO SDK.

Buckets are created once on first boot by the ``minio-init`` service in
``docker-compose.yml`` — we don't try to create them here.

This module exposes a single module-level ``minio_client`` (sync) — the
SDK itself is not async, so wrapping in asyncio.to_thread() at the
call-site is the recommended pattern when used from FastAPI.
"""

from __future__ import annotations

import contextlib
from datetime import timedelta
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


def presigned_get_url(
    bucket: str,
    object_key: str,
    expires_seconds: int = 300,
) -> str:
    """Time-limited URL the browser can hit directly to download a private object.

    Returned URL points at the *public* MinIO endpoint (``localhost:8302``
    in dev), so the SDK-signed host header has to be rewritten — we do
    that by building the client against the public endpoint just for
    signing. Default TTL is 5 minutes; the caller can extend it for
    cases like resuming a multi-gigabyte download.
    """
    # We need a client bound to the public endpoint, otherwise the
    # signed URL would point at "minio:9000" which is unreachable from
    # the user's browser.
    public_host = settings.MINIO_PUBLIC_ENDPOINT.split("://", 1)[-1]
    signing_client = Minio(
        endpoint=public_host,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_PUBLIC_ENDPOINT.startswith("https://"),
    )
    return signing_client.presigned_get_object(
        bucket, object_key, expires=timedelta(seconds=expires_seconds)
    )


def get_bytes(bucket: str, object_key: str) -> bytes:
    """Read an object from MinIO into memory.

    Used by Celery tasks that need to operate on the bytes (e.g. demo PDF
    extraction). Don't call this for large files in user-facing handlers —
    use signed URLs instead.
    """
    response = minio_client.get_object(bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def stream_object(bucket: str, object_key: str, chunk_size: int = 64 * 1024):
    """Yield ``object_key`` in chunks for a streaming HTTP response.

    The caller is responsible for closing the underlying connection — we
    handle it inside the generator's ``finally`` so a disconnect mid-
    stream still releases the pool slot.
    """
    response = minio_client.get_object(bucket, object_key)
    try:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        response.close()
        response.release_conn()


def stat_object(bucket: str, object_key: str):
    """Lightweight HEAD — returns content length, last-modified, etag."""
    return minio_client.stat_object(bucket, object_key)
