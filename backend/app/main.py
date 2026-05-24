import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter, rate_limit_exceeded_handler

logger = logging.getLogger("monografiya")
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _init_sentry() -> None:
    """Wire Sentry only when a DSN is configured.

    Skipping the call when the DSN is blank means dev/test runs don't
    accidentally ship local errors upstream, and unit tests stay
    sentry-free without monkey-patching anything.
    """
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            release=__version__,
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            # 10% of requests get traced — bump if traffic is light, drop
            # if Sentry quota starts hurting.
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry initialised env=%s", settings.SENTRY_ENVIRONMENT)
    except Exception:  # noqa: BLE001
        logger.exception("Sentry init failed — continuing without it")


_init_sentry()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting monografiya backend (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down monografiya backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Monografiya API",
        version=__version__,
        description="Monografiya sotuvi platformasi — REST API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Rate limiting — registered before CORS so 429s still include CORS headers
    # (handlers run inside-out).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        """OWASP basics. CSP is intentionally relaxed in dev so Swagger UI
        keeps working — production layers a strict CSP via Nginx."""
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

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
            "message": "Monografiya API",
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # SEO routes mount at the application root (no /api/v1 prefix) so
    # crawlers can hit /sitemap.xml + /robots.txt directly.
    from app.api.v1.endpoints import seo

    app.include_router(seo.router)

    return app


app = create_app()
