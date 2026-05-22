"""Production seed — categories only.

Idempotent: re-running picks up where it left off. No users, no books,
no author profiles — those land via the regular sign-up + publish flow.

Usage::

    docker compose -f docker-compose.prod.yml exec backend \
        python -m app.scripts.seed_categories
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import Category

logger = logging.getLogger("seed_categories")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [seed] %(message)s")


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


async def _get_category(db: AsyncSession, slug: str) -> Category | None:
    return (
        await db.execute(select(Category).where(Category.slug == slug))
    ).scalar_one_or_none()


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        by_slug: dict[str, UUID] = {}

        for slug, parent_slug, name, icon, sort in CATEGORIES:
            existing = await _get_category(db, slug)
            if existing is not None:
                by_slug[slug] = existing.id
                logger.info("category %s exists", slug)
                continue

            parent_id = by_slug.get(parent_slug) if parent_slug else None
            row = Category(
                slug=slug,
                name=name,
                parent_id=parent_id,
                icon=icon,
                sort_order=sort,
                is_active=True,
            )
            db.add(row)
            await db.flush()
            by_slug[slug] = row.id
            logger.info("category %s created", slug)

        await db.commit()
        logger.info("seeded %s categories", len(by_slug))


if __name__ == "__main__":
    asyncio.run(seed())
