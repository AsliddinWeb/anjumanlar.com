"""Top-level v1 router.

Sub-routers (auth, books, orders, etc.) will be added in Phase 1+.
For now we only expose a single readiness probe so the v1 surface is
discoverable in Swagger.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
