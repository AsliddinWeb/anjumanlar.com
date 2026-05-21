"""Top-level v1 router. Sub-routers register here so Swagger sees them all."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import auth, authors, books, categories, reviews, search, users
from app.db.session import get_db

api_router = APIRouter()


@api_router.get("/ping", tags=["meta"])
async def ping() -> dict[str, str]:
    return {"pong": "ok"}


@api_router.get("/ready", tags=["meta"])
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    """Readiness probe — fails if the DB is unreachable."""
    result = await db.execute(text("SELECT 1"))
    db_ok = result.scalar_one() == 1
    return {"ready": db_ok, "db": "ok" if db_ok else "fail"}


api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(authors.router)
api_router.include_router(categories.router)
api_router.include_router(books.router)
api_router.include_router(reviews.books_review_router)
api_router.include_router(reviews.review_router)
api_router.include_router(reviews.admin_review_router)
api_router.include_router(search.router)
