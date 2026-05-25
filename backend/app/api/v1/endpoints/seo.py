"""Public SEO endpoints — sitemap.xml + robots.txt.

These live under the v1 prefix because the rest of the API does and
because nginx already proxies /api/v1 to FastAPI. Nginx rewrites the
top-level ``/sitemap.xml`` + ``/robots.txt`` paths to these handlers
in production (see ``nginx/conf.d/monografiya.com.conf``).

The sitemap is generated lazily on each request and includes:

- 3 locale variants of every static page (/, /books, /authors, …)
- 3 locale variants of every approved book (last-modified =
  ``Book.updated_at``)
- 3 locale variants of every author profile
- 3 locale variants of every active category

For a marketplace with tens of thousands of rows we'd swap this for a
cron-built static file; under that size the live query is fine.
"""

from __future__ import annotations

from datetime import datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models import (
    AuthorProfile,
    BlogPost,
    BlogPostStatus,
    Book,
    BookStatus,
    Category,
)

router = APIRouter(tags=["seo"])

LOCALES = ("uz", "ru", "en")
STATIC_PATHS = ("/", "/books", "/authors", "/about", "/blog")


def _site_url() -> str:
    return settings.FRONTEND_URL.rstrip("/")


def _iso(dt: datetime | None) -> str:
    return (dt or datetime.utcnow()).strftime("%Y-%m-%d")


def _url_entry(loc: str, lastmod: str | None, priority: float) -> str:
    parts = [
        "  <url>",
        f"    <loc>{escape(loc)}</loc>",
    ]
    if lastmod:
        parts.append(f"    <lastmod>{lastmod}</lastmod>")
    parts.append(f"    <priority>{priority:.1f}</priority>")
    parts.append("  </url>")
    return "\n".join(parts)


@router.get(
    "/sitemap.xml",
    summary="Dynamic sitemap covering every public page",
    include_in_schema=False,
)
async def sitemap(db: AsyncSession = Depends(get_db)) -> Response:
    site = _site_url()
    entries: list[str] = []

    # --- Static pages -----------------------------------------------------
    for path in STATIC_PATHS:
        for lang in LOCALES:
            entries.append(
                _url_entry(
                    loc=f"{site}/{lang}{path}".rstrip("/")
                    if path == "/"
                    else f"{site}/{lang}{path}",
                    lastmod=None,
                    priority=1.0 if path == "/" else 0.7,
                )
            )

    # --- Books ------------------------------------------------------------
    book_rows = (
        (
            await db.execute(
                select(Book.slug, Book.updated_at).where(
                    Book.status == BookStatus.approved,
                )
            )
        )
        .all()
    )
    for slug, updated_at in book_rows:
        for lang in LOCALES:
            entries.append(
                _url_entry(
                    loc=f"{site}/{lang}/books/{slug}",
                    lastmod=_iso(updated_at),
                    priority=0.8,
                )
            )

    # --- Categories -------------------------------------------------------
    cat_rows = (
        (
            await db.execute(
                select(Category.slug, Category.created_at).where(
                    Category.is_active.is_(True)
                )
            )
        )
        .all()
    )
    for slug, created_at in cat_rows:
        for lang in LOCALES:
            entries.append(
                _url_entry(
                    loc=f"{site}/{lang}/category/{slug}",
                    lastmod=_iso(created_at),
                    priority=0.6,
                )
            )

    # --- Blog posts -------------------------------------------------------
    blog_rows = (
        (
            await db.execute(
                select(BlogPost.slug, BlogPost.published_at, BlogPost.updated_at).where(
                    BlogPost.status == BlogPostStatus.published
                )
            )
        )
        .all()
    )
    for slug, published_at, updated_at in blog_rows:
        for lang in LOCALES:
            entries.append(
                _url_entry(
                    loc=f"{site}/{lang}/blog/{slug}",
                    lastmod=_iso(updated_at or published_at),
                    priority=0.6,
                )
            )

    # --- Authors ----------------------------------------------------------
    author_rows = (
        (
            await db.execute(
                select(AuthorProfile.slug, AuthorProfile.updated_at)
            )
        )
        .all()
    )
    for slug, updated_at in author_rows:
        for lang in LOCALES:
            entries.append(
                _url_entry(
                    loc=f"{site}/{lang}/authors/{slug}",
                    lastmod=_iso(updated_at),
                    priority=0.5,
                )
            )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


@router.get(
    "/robots.txt",
    summary="robots.txt — disallow private paths, point at sitemap",
    include_in_schema=False,
)
async def robots() -> Response:
    site = _site_url()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /account\n"
        "Disallow: /auth\n"
        "Disallow: /checkout\n"
        "Disallow: /cart\n"
        "Disallow: /search\n"
        "\n"
        f"Sitemap: {site}/sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain")
