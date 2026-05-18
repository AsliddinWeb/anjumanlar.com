from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- General -----
    PROJECT_NAME: str = "anjumanlar"
    ENVIRONMENT: Environment = "development"
    TZ: str = "Asia/Tashkent"
    API_V1_PREFIX: str = "/api/v1"

    # ----- Database -----
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://anjumanlar:anjumanlar@postgres:5432/anjumanlar"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://anjumanlar:anjumanlar@postgres:5432/anjumanlar"
    )
    DATABASE_ECHO: bool = False

    # ----- Redis / Celery -----
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ----- MinIO -----
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://localhost:8302"
    MINIO_ROOT_USER: str = "minio-root"
    MINIO_ROOT_PASSWORD: str = "minio-root-pass"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_BOOKS: str = "books"
    MINIO_BUCKET_BOOKS_WM: str = "books-watermarked"
    MINIO_BUCKET_COVERS: str = "covers"
    MINIO_BUCKET_AVATARS: str = "avatars"
    MINIO_BUCKET_DEMOS: str = "demos"
    MINIO_BUCKET_BLOG: str = "blog"

    # ----- Meilisearch -----
    MEILISEARCH_URL: str = "http://meilisearch:7700"
    MEILISEARCH_MASTER_KEY: str = "change-me-32-chars-minimum-secret-key"

    # ----- JWT -----
    JWT_SECRET_KEY: str = "change-me-generate-with-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ----- Email -----
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = False
    EMAIL_FROM: str = "noreply@anjumanlar.com"
    EMAIL_FROM_NAME: str = "Anjumanlar.com"

    # ----- Payme -----
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""
    PAYME_ENDPOINT: str = "https://checkout.test.paycom.uz/api"
    PAYME_CHECKOUT_URL: str = "https://checkout.test.paycom.uz"

    # ----- CORS -----
    CORS_ORIGINS: str = "http://localhost:8308,http://127.0.0.1:8308"

    # ----- Sentry -----
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"

    # ----- Limits -----
    MAX_BOOK_FILE_MB: int = 100
    MAX_DEMO_FILE_MB: int = 20
    MAX_COVER_FILE_MB: int = 5
    MAX_AVATAR_FILE_MB: int = 2

    # ----- Site URLs -----
    FRONTEND_URL: str = "http://localhost:8308"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
