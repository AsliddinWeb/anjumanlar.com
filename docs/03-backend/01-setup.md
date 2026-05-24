# 01. Backend O'rnatish va Sozlash

> FastAPI loyihasini noldan ishga tushirish bo'yicha to'liq qo'llanma.

---

## 🐍 Talablar

- Python 3.12+
- pip yoki uv
- PostgreSQL 16 (Docker bilan o'rnatamiz)
- Redis 7 (Docker bilan)
- Git

---

## 📦 1-qadam: Loyihani yaratish

```bash
# Asosiy papka
mkdir -p monografiya/backend
cd monografiya/backend

# Virtual environment
python3.12 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Yoki uv ishlatish (tezroq):
# uv venv && source .venv/bin/activate
```

---

## 📋 2-qadam: `pyproject.toml`

```toml
[project]
name = "monografiya-backend"
version = "0.1.0"
description = "Monografiya — monografiya marketplace backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "celery>=5.3.6",
    "redis>=5.0.1",
    "minio>=7.2.0",
    "meilisearch>=0.31.0",
    "httpx>=0.26.0",
    "Pillow>=10.2.0",
    "pypdf>=4.0.0",
    "reportlab>=4.0.9",
    "email-validator>=2.1.0",
    "aiosmtplib>=3.0.1",
    "slowapi>=0.1.9",
    "jinja2>=3.1.3",
    "loguru>=0.7.2",
    "sentry-sdk[fastapi]>=1.40.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "factory-boy>=3.3.0",
    "faker>=22.0.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]
```

```bash
pip install -e ".[dev]"
# yoki uv pip install -e ".[dev]"
```

---

## 🏗 3-qadam: Asosiy struktura yaratish

```bash
mkdir -p app/{api/v1/endpoints,core,db,models,schemas,services,integrations/payme,tasks,locale,scripts}
mkdir -p alembic/versions tests
touch app/__init__.py app/main.py app/config.py app/dependencies.py
```

---

## ⚙️ 4-qadam: `app/config.py` (sozlamalar)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Asosiy
    APP_NAME: str = "Monografiya"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str  # .env dan keladi

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://monografiya.com",
    ]

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "monografiya"
    MINIO_SECURE: bool = False  # production'da True

    # Meilisearch
    MEILISEARCH_URL: str = "http://meilisearch:7700"
    MEILISEARCH_KEY: str

    # Payme
    PAYME_MERCHANT_ID: str
    PAYME_SECRET_KEY: str
    PAYME_ENDPOINT: str = "https://checkout.paycom.uz/api"
    PAYME_TEST_MODE: bool = True

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str = "noreply@monografiya.com"
    SMTP_FROM_NAME: str = "Monografiya"

    # Frontend URL (emaillar uchun)
    FRONTEND_URL: str = "https://monografiya.com"

    # Komissiya
    DEFAULT_COMMISSION_PERCENT: float = 15.0

    # Sentry
    SENTRY_DSN: str | None = None


settings = Settings()
```

---

## 🚀 5-qadam: `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import sentry_sdk

from app.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import limiter


# Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.APP_ENV,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 {settings.APP_NAME} started in {settings.APP_ENV} mode")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Monografiya marketplace API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
setup_exception_handlers(app)

# Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

## 🗄 6-qadam: `app/db/session.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 📝 7-qadam: `app/db/base.py`

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid


class Base(DeclarativeBase):
    """Asosiy SQLAlchemy Base klassi."""
    pass


class TimestampMixin:
    """Yaratilgan va yangilangan vaqtlar."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def generate_uuid() -> str:
    return str(uuid.uuid4())
```

---

## 🔐 8-qadam: `app/core/security.py`

```python
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
```

---

## 🔄 9-qadam: Alembic (migration)

```bash
cd backend
alembic init alembic
```

`alembic/env.py` ni o'zgartiring:

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.db.base import Base
# Modellarni import qilish (yo'qsa avto-generation ishlamaydi)
from app.models import user, book, category, order, payment, review  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
```

---

## 🐳 10-qadam: `Dockerfile`

```dockerfile
FROM python:3.12-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🔧 11-qadam: `.env.example`

```bash
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=change-this-to-random-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://monografiya:password@postgres:5432/monografiya

# JWT
JWT_SECRET_KEY=another-random-secret-for-jwt
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=monografiya

# Meilisearch
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_KEY=masterKey

# Payme
PAYME_MERCHANT_ID=your-merchant-id
PAYME_SECRET_KEY=your-payme-secret
PAYME_TEST_MODE=true

# SMTP (Brevo, Mailgun yoki Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@monografiya.com

# Frontend
FRONTEND_URL=http://localhost:3000

# Sentry (ixtiyoriy)
SENTRY_DSN=
```

---

## ▶️ 12-qadam: Ishga tushirish

```bash
# Docker compose orqali (tavsiya etilgan)
docker compose up backend postgres redis

# Yoki lokalda
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Migration yaratish
alembic revision --autogenerate -m "Initial migration"

# Migration qo'llash
alembic upgrade head

# Brauzerda:
# http://localhost:8000/docs
```

---

## ✅ Tekshiruv ro'yxati

- [ ] Python 3.12+ o'rnatilgan
- [ ] Virtual env yaratilgan
- [ ] Dependencies o'rnatilgan
- [ ] `.env` fayl yaratilgan va to'ldirilgan
- [ ] PostgreSQL ishlamoqda
- [ ] Redis ishlamoqda
- [ ] Migration muvaffaqiyatli
- [ ] `http://localhost:8000/docs` ochiladi
- [ ] `http://localhost:8000/health` ishlaydi

---

**Keyingi qadam:** [`02-api-endpoints.md`](./02-api-endpoints.md) — Barcha API endpointlar.
