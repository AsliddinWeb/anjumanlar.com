import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger("anjumanlar")
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting anjumanlar backend (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down anjumanlar backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Anjumanlar.com API",
        version=__version__,
        description="Monografiya sotuvi platformasi — REST API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.PROJECT_NAME,
            "version": __version__,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/", tags=["meta"], include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "message": "Anjumanlar.com API",
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
