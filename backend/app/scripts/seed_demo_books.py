"""Production demo seed — 2 authors + 4 approved books.

Idempotent. Assumes ``seed_categories`` has already been run; otherwise
the script ensures the categories it needs exist by slug (mirroring the
production list).

Usage::

    docker compose -f docker-compose.prod.yml exec backend \
        python -m app.scripts.seed_demo_books

What it does:
  1. Make sure the 2 demo authors have user accounts + author_profiles.
  2. Add 4 books, all approved + published, varied across categories
     and price tiers (1 free, 3 paid).
  3. Push each book into Meilisearch synchronously so /search works
     immediately without waiting for Celery.

Default password for both demo authors: ``DemoAuthor!2026``.
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

logger = logging.getLogger("seed_demo_books")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [seed] %(message)s")

DEFAULT_PASSWORD = "DemoAuthor!2026"


AUTHORS = [
    # (email, full_name, slug, bio_uz, institution, academic_title)
    (
        "demo.kardiolog@monografiya.com",
        "Dilshod Razzakov",
        "dilshod-razzakov",
        "Tibbiyot fanlari nomzodi, kardiolog. 15 yillik amaliy tajriba.",
        "Toshkent tibbiyot akademiyasi",
        "Tib. fan. nomzodi",
    ),
    (
        "demo.iqtisodchi@monografiya.com",
        "Malika Toshpulatova",
        "malika-toshpulatova",
        "Iqtisod fanlari professori, makroiqtisod sohasida 50+ maqola muallifi.",
        "Toshkent davlat iqtisodiyot universiteti",
        "Professor",
    ),
]


BOOKS = [
    # (slug, author_slug, category_slugs, title, description, language, price, featured)
    (
        "kardiologiya-amaliyoti-2026",
        "dilshod-razzakov",
        ["tibbiyot", "kardiologiya"],
        {
            "uz": "Kardiologiya amaliyoti — 2026",
            "ru": "Практическая кардиология — 2026",
            "en": "Practical Cardiology — 2026",
        },
        {
            "uz": "Yurak-qon tomir kasalliklarining diagnostikasi va davolanishi. EKG tahlili, ehokardiografiya, klinik holatlar va zamonaviy davo standartlari.",
            "ru": "Диагностика и лечение сердечно-сосудистых заболеваний. ЭКГ, эхокардиография, клинические случаи и современные протоколы лечения.",
        },
        BookLanguage.uz,
        85000,
        True,
    ),
    (
        "makroiqtisod-2026",
        "malika-toshpulatova",
        ["iqtisod", "makroiqtisod"],
        {
            "uz": "Makroiqtisodiyot 2026",
            "ru": "Макроэкономика 2026",
            "en": "Macroeconomics 2026",
        },
        {
            "uz": "Zamonaviy makroiqtisodiy nazariyalar va ularning O'zbekistondagi tatbiqi. Pul-kredit siyosati, inflatsiya, ish bilan bandlik va o'sish modellari.",
        },
        BookLanguage.mixed,
        65000,
        True,
    ),
    (
        "tezkor-diagnostika-asoslari",
        "dilshod-razzakov",
        ["tibbiyot"],
        {
            "uz": "Tezkor diagnostika asoslari",
            "ru": "Основы экстренной диагностики",
        },
        {
            "uz": "Tez tibbiy yordam holatlarida birinchi tashxis qo'yish bo'yicha qo'llanma. Belgilar, tezkor testlar, qaror daraxti.",
        },
        BookLanguage.uz,
        45000,
        False,
    ),
    (
        "iqtisod-bepul-kirish-darsligi",
        "malika-toshpulatova",
        ["iqtisod"],
        {
            "uz": "Iqtisodga bepul kirish darsligi",
            "en": "Free Introduction to Economics",
        },
        {
            "uz": "Bakalavr 1-kurs talabalari uchun bepul kirish kursi. Talab va taklif, bozor mexanizmlari, asosiy modellar.",
        },
        BookLanguage.uz,
        0,
        False,
    ),
]


async def _get_user(db: AsyncSession, email: str) -> User | None:
    return (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def _get_author(db: AsyncSession, slug: str) -> AuthorProfile | None:
    return (
        await db.execute(select(AuthorProfile).where(AuthorProfile.slug == slug))
    ).scalar_one_or_none()


async def _get_book(db: AsyncSession, slug: str) -> Book | None:
    return (await db.execute(select(Book).where(Book.slug == slug))).scalar_one_or_none()


async def _get_category(db: AsyncSession, slug: str) -> Category | None:
    return (await db.execute(select(Category).where(Category.slug == slug))).scalar_one_or_none()


async def seed_authors(db: AsyncSession) -> dict[str, UUID]:
    by_slug: dict[str, UUID] = {}
    for email, full_name, slug, bio, institution, title in AUTHORS:
        profile = await _get_author(db, slug)
        if profile is not None:
            by_slug[slug] = profile.id
            logger.info("author %s already exists", slug)
            continue

        user = await _get_user(db, email)
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

        profile = AuthorProfile(
            user_id=user.id,
            slug=slug,
            display_name=full_name,
            bio={"uz": bio},
            institution=institution,
            academic_title=title,
            verified=True,
        )
        db.add(profile)
        await db.flush()
        by_slug[slug] = profile.id
        logger.info("author %s created (email=%s, password=%r)", slug, email, DEFAULT_PASSWORD)
    return by_slug


async def seed_books(db: AsyncSession, author_ids: dict[str, UUID]) -> None:
    from app.integrations.meilisearch_client import upsert_book_document
    from app.services import search_service

    for (slug, author_slug, cat_slugs, title, description, language, price, featured) in BOOKS:
        if await _get_book(db, slug) is not None:
            logger.info("book %s already exists", slug)
            continue

        cats: list[Category] = []
        for cs in cat_slugs:
            c = await _get_category(db, cs)
            if c is None:
                logger.warning("skipping category %s (not seeded yet)", cs)
                continue
            cats.append(c)
        if not cats:
            logger.warning("book %s skipped — none of its categories exist; run seed_categories first", slug)
            continue

        author_profile_id = author_ids[author_slug]
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
            status=BookStatus.approved,
            featured=featured,
            publication_year=2026,
            publisher="Monografiya seed",
            published_at=datetime.now(UTC),
        )
        book.categories = cats
        db.add(book)
        await db.flush()

        # Synchronous Meilisearch push — /search works right after seeding,
        # no need to wait for Celery.
        await db.refresh(book, ["author", "categories"])
        try:
            upsert_book_document(search_service.book_to_document(book))
        except Exception:
            logger.exception("meilisearch sync failed for %s (continuing)", slug)

        logger.info("book %s created (price=%s, featured=%s)", slug, price, featured)


async def main() -> None:
    async with AsyncSessionLocal() as db:
        author_ids = await seed_authors(db)
        await seed_books(db, author_ids)
        await db.commit()
    logger.info("done — 4 demo books seeded. Authors login: %r", DEFAULT_PASSWORD)


if __name__ == "__main__":
    asyncio.run(main())
