# Migratsiyalar — Alembic

Alembic — SQLAlchemy uchun rasmiy migration tool. PostgreSQL schema o'zgarishlarini versiya qiluvchi tizim.

## Sozlash

```bash
cd backend
alembic init -t async alembic
```

Bu `alembic/` papkasini va `alembic.ini` faylini yaratadi.

## alembic.ini (asosiy qismlari)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# DB URL .env'dan o'qiladi
sqlalchemy.url = 

[loggers]
keys = root,sqlalchemy,alembic

[logger_root]
level = WARN
handlers = console
```

## alembic/env.py

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.base import Base

# Barcha modellar bu yerga import qilinadi (autogenerate uchun)
from app.models import (  # noqa
    user, author_profile, book, category, order, payment,
    review, wishlist, user_library, withdrawal, blog_post,
    setting, notification, audit_log, refresh_token,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Asosiy buyruqlar

### Yangi migratsiya yaratish (autogenerate)

```bash
alembic revision --autogenerate -m "create users table"
```

Bu `alembic/versions/` ga yangi fayl qo'shadi. **Avtomatik yaratilgan migratsiyani har doim qo'lda tekshiring.**

### Migratsiyani qo'llash

```bash
# Eng oxirgi versiyaga
alembic upgrade head

# Aniq versiyaga
alembic upgrade <revision_id>

# 1 ta qadam oldinga
alembic upgrade +1
```

### Orqaga qaytarish

```bash
# 1 qadam orqaga
alembic downgrade -1

# Aniq versiyaga
alembic downgrade <revision_id>

# Boshlang'ichga
alembic downgrade base
```

### Tarix va holat

```bash
alembic current        # joriy versiya
alembic history        # barcha versiyalar
alembic heads          # branchlar (agar bor bo'lsa)
```

## SQLAlchemy Model misoli

### app/models/user.py

```python
import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    author = "author"
    reader = "reader"


class UserStatus(str, enum.Enum):
    active = "active"
    pending = "pending"
    blocked = "blocked"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.reader, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"), default=UserStatus.pending, nullable=False
    )
    preferred_locale: Mapped[str] = mapped_column(String(5), default="uz")
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    author_profile = relationship("AuthorProfile", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    library = relationship("UserLibrary", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")
```

### app/models/book.py (qisqartirilgan)

```python
import enum
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import (
    String, Text, Integer, Numeric, Boolean, DateTime,
    Enum, ForeignKey, ARRAY, func, Computed,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BookStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("author_profiles.id"), nullable=False
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[dict] = mapped_column(JSONB, nullable=False)
    subtitle: Mapped[dict] = mapped_column(JSONB, default=dict)
    description: Mapped[dict] = mapped_column(JSONB, default=dict)
    isbn: Mapped[str | None] = mapped_column(String(20))
    pages_count: Mapped[int | None] = mapped_column(Integer)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    file_url: Mapped[str | None] = mapped_column(String(500))
    demo_url: Mapped[str | None] = mapped_column(String(500))
    
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_free: Mapped[bool] = mapped_column(
        Boolean, Computed("price = 0", persisted=True)
    )
    
    status: Mapped[BookStatus] = mapped_column(
        Enum(BookStatus, name="book_status"), default=BookStatus.draft
    )
    
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    author = relationship("AuthorProfile", back_populates="books")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    categories = relationship("Category", secondary="book_categories", back_populates="books")
    reviews = relationship("Review", back_populates="book")
```

## Birinchi migratsiya — boshlang'ich schema

```bash
# Modellar yaratilgandan keyin:
alembic revision --autogenerate -m "initial schema"
```

Yaratiladi: `alembic/versions/2025_01_15_1200-abc123_initial_schema.py`

Faylni tekshiring va kerak bo'lsa qo'shing:
- Trigger'lar (yuqorida ko'rsatilgan)
- Custom indekslar
- Extension yaratish:

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    # ... qolgan migratsiya
```

## Production'da migratsiya

```bash
# Avval backup oling
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Migratsiyani sinab ko'ring (dry-run)
alembic upgrade head --sql > migration.sql
# faylni tekshiring

# Qo'llang
alembic upgrade head
```

## Best practices

1. **Hech qachon o'tgan migratsiyani o'zgartirmang** — yangi migratsiya yarating.
2. **Har migratsiyani lokal va staging'da sinang** production'dan oldin.
3. **Data migration'lar uchun** — schema va data o'zgarishlarini alohida fayllarda.
4. **Migrate buyruqlari Docker entrypoint'da:**
   ```bash
   alembic upgrade head && uvicorn app.main:app
   ```
5. **Branch'lar — git'da konflikt bo'lsa** `alembic merge` bilan birlashtiring.

**Keyingi qadam:** `05-database/03-seed-data.md`
