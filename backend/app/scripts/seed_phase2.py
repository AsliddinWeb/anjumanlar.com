"""Seed Phase 2 dev data: categories + a few authors + demo books.

Idempotent — re-running picks up where it left off and skips anything
that already exists, so it's safe to call from ``make seed`` repeatedly.

Usage::

    docker compose exec backend python -m app.scripts.seed_phase2
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
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

logger = logging.getLogger("seed_phase2")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [seed] %(message)s")

DEFAULT_PASSWORD = "SeedPass99!"


# ---------- raw data ----------


CATEGORIES = [
    # (slug, parent_slug, name_dict, icon, sort_order)
    ("tibbiyot", None, {"uz": "Tibbiyot", "ru": "Медицина", "en": "Medicine"}, "🩺", 1),
    ("iqtisod", None, {"uz": "Iqtisod", "ru": "Экономика", "en": "Economics"}, "📈", 2),
    ("filologiya", None, {"uz": "Filologiya", "ru": "Филология", "en": "Philology"}, "📚", 3),
    ("tarix", None, {"uz": "Tarix", "ru": "История", "en": "History"}, "🏺", 4),
    ("muhandislik", None, {"uz": "Muhandislik", "ru": "Инженерия", "en": "Engineering"}, "🛠", 5),
    (
        "kompyuter-fanlari",
        None,
        {"uz": "Kompyuter fanlari", "ru": "Информатика", "en": "Computer Science"},
        "💻",
        6,
    ),
    ("huquq", None, {"uz": "Huquq", "ru": "Право", "en": "Law"}, "⚖", 7),
    ("falsafa", None, {"uz": "Falsafa", "ru": "Философия", "en": "Philosophy"}, "🦉", 8),
    # Children
    (
        "kardiologiya",
        "tibbiyot",
        {"uz": "Kardiologiya", "ru": "Кардиология", "en": "Cardiology"},
        None,
        1,
    ),
    (
        "makroiqtisod",
        "iqtisod",
        {"uz": "Makroiqtisodiyot", "ru": "Макроэкономика", "en": "Macroeconomics"},
        None,
        1,
    ),
]


AUTHORS = [
    # (email, full_name, display_name, slug, bio_uz, institution, academic_title)
    (
        "aziz.karimov@example.com",
        "Aziz Karimov",
        "Aziz Karimov",
        "aziz-karimov",
        "Tarix fanlari doktori, 20+ yillik tadqiqot tajribasiga ega.",
        "O'zbekiston Milliy Universiteti",
        "PhD",
    ),
    (
        "dilshod.razzakov@example.com",
        "Dilshod Razzakov",
        "Dilshod Razzakov",
        "dilshod-razzakov",
        "Tibbiyot fanlari nomzodi, kardiolog.",
        "Toshkent tibbiyot akademiyasi",
        "Tib. fan. nomzodi",
    ),
    (
        "malika.toshpulatova@example.com",
        "Malika Toshpulatova",
        "Malika Toshpulatova",
        "malika-toshpulatova",
        "Iqtisod fanlari professori, makroiqtisod sohasida 50+ maqola muallifi.",
        "Toshkent davlat iqtisodiyot universiteti",
        "Professor",
    ),
]


BOOKS = [
    # (slug, author_slug, category_slugs, title, description, language, price, status, featured)
    (
        "tarix-asoslari-2026",
        "aziz-karimov",
        ["tarix"],
        {"uz": "Tarix asoslari", "ru": "Основы истории", "en": "Foundations of History"},
        {
            "uz": "O'zbekiston tarixiga oid yangi yondashuvlar.",
            "en": "New approaches to the history of Uzbekistan.",
        },
        BookLanguage.uz,
        50000,
        BookStatus.approved,
        True,
    ),
    (
        "kardiologiya-amaliyoti",
        "dilshod-razzakov",
        ["tibbiyot", "kardiologiya"],
        {"uz": "Kardiologiya amaliyoti", "ru": "Практическая кардиология"},
        {"uz": "Yurak-qon tomir kasalliklarining diagnostikasi va davolanishi."},
        BookLanguage.uz,
        80000,
        BookStatus.approved,
        True,
    ),
    (
        "makroiqtisod-2026",
        "malika-toshpulatova",
        ["iqtisod", "makroiqtisod"],
        {"uz": "Makroiqtisodiyot 2026", "ru": "Макроэкономика 2026", "en": "Macroeconomics 2026"},
        {"uz": "Zamonaviy makroiqtisodiy nazariyalar va O'zbekistondagi tatbiqi."},
        BookLanguage.mixed,
        65000,
        BookStatus.approved,
        False,
    ),
    (
        "bepul-tarix-darsligi",
        "aziz-karimov",
        ["tarix"],
        {"uz": "Bepul tarix darsligi", "en": "Free History Textbook"},
        {"uz": "Talabalar uchun bepul kirish darsligi."},
        BookLanguage.uz,
        0,
        BookStatus.approved,
        False,
    ),
    (
        "moliyaviy-tahlil-asoslari",
        "malika-toshpulatova",
        ["iqtisod"],
        {"uz": "Moliyaviy tahlil asoslari"},
        {"uz": "Hali tahrir bosqichida — yakunlanmoqda."},
        BookLanguage.uz,
        70000,
        BookStatus.draft,
        False,
    ),
]


# ---------- helpers ----------


async def _get_category(db: AsyncSession, slug: str) -> Category | None:
    return (await db.execute(select(Category).where(Category.slug == slug))).scalar_one_or_none()


async def _get_author(db: AsyncSession, slug: str) -> AuthorProfile | None:
    return (
        await db.execute(select(AuthorProfile).where(AuthorProfile.slug == slug))
    ).scalar_one_or_none()


async def _get_book(db: AsyncSession, slug: str) -> Book | None:
    return (await db.execute(select(Book).where(Book.slug == slug))).scalar_one_or_none()


# ---------- seeders ----------


async def seed_categories(db: AsyncSession) -> dict[str, UUID]:
    """Two-pass: roots first, then children that reference them by slug."""
    by_slug: dict[str, UUID] = {}

    for slug, parent_slug, name, icon, sort in CATEGORIES:
        existing = await _get_category(db, slug)
        if existing is not None:
            by_slug[slug] = existing.id
            continue
        parent_id = by_slug.get(parent_slug) if parent_slug else None
        cat = Category(
            slug=slug,
            name=name,
            parent_id=parent_id,
            icon=icon,
            sort_order=sort,
            is_active=True,
        )
        db.add(cat)
        await db.flush()
        by_slug[slug] = cat.id
        logger.info("category %s created", slug)
    return by_slug


async def seed_authors(db: AsyncSession) -> dict[str, UUID]:
    """User + author_profile per row. Idempotent by email."""
    by_slug: dict[str, UUID] = {}
    for email, full_name, display_name, slug, bio, institution, title in AUTHORS:
        profile = await _get_author(db, slug)
        if profile is not None:
            by_slug[slug] = profile.id
            continue

        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(DEFAULT_PASSWORD),
                full_name=full_name,
                role=UserRole.author,
                status=UserStatus.active,
                email_verified=True,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)

        profile = AuthorProfile(
            user_id=user.id,
            slug=slug,
            display_name=display_name,
            bio={"uz": bio},
            institution=institution,
            academic_title=title,
            verified=True,
        )
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
        by_slug[slug] = profile.id
        logger.info("author %s created (email=%s)", slug, email)
    return by_slug


async def seed_books(
    db: AsyncSession,
    cat_ids: dict[str, UUID],
    author_ids: dict[str, UUID],
) -> None:
    """One pass — each book references its author + categories by slug."""
    for (
        slug,
        author_slug,
        cat_slugs,
        title,
        description,
        language,
        price,
        status,
        featured,
    ) in BOOKS:
        if await _get_book(db, slug) is not None:
            continue

        author_profile_id = author_ids[author_slug]
        # The book's ``uploaded_by`` must be the author's user — fetch it.
        author = (
            await db.execute(select(AuthorProfile).where(AuthorProfile.id == author_profile_id))
        ).scalar_one()

        book = Book(
            author_id=author_profile_id,
            uploaded_by=author.user_id,
            slug=slug,
            title=title,
            description=description,
            language=language,
            price=price,
            status=status,
            featured=featured,
            publication_year=2026,
            publisher="Seed nashriyoti",
            published_at=datetime.now(UTC) if status == BookStatus.approved else None,
        )
        cats = [
            (await db.execute(select(Category).where(Category.id == cat_ids[s]))).scalar_one()
            for s in cat_slugs
        ]
        book.categories = cats
        db.add(book)
        await db.flush()
        logger.info("book %s created (status=%s)", slug, status.value)

        # Push approved books to Meilisearch immediately so /search works
        # right after seeding (the Celery worker may not even be up yet).
        if status == BookStatus.approved:
            from app.integrations.meilisearch_client import upsert_book_document
            from app.services import search_service

            await db.refresh(book, ["author", "categories"])
            try:
                upsert_book_document(search_service.book_to_document(book))
            except Exception:
                logger.exception("seed: meilisearch sync failed for %s", slug)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        cat_ids = await seed_categories(session)
        author_ids = await seed_authors(session)
        await seed_books(session, cat_ids, author_ids)
        await session.commit()
    logger.info("seed_phase2 done — login as any seeded author with password %r", DEFAULT_PASSWORD)


if __name__ == "__main__":
    asyncio.run(main())
