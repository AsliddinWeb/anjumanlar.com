# Monografiya Backend (FastAPI)

REST API for monografiya.com — Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Celery.

## Local development

The backend runs inside Docker via the root `docker-compose.yml`. From repo root:

```bash
make up                # starts postgres + redis + minio + meili + mailhog + backend
make logs s=backend    # tail backend logs
make migrate           # alembic upgrade head
make test              # pytest
```

Open:
- Swagger: <http://localhost:8307/docs>
- Health:  <http://localhost:8307/health>
- Ping:    <http://localhost:8307/api/v1/ping>
- Ready:   <http://localhost:8307/api/v1/ready>

## Package layout

```
app/
├── main.py             FastAPI factory + /health
├── config.py           pydantic-settings reading .env
├── api/v1/
│   ├── router.py       v1 router aggregator
│   └── endpoints/      per-resource routers (added in Phase 1+)
├── core/
│   ├── exceptions.py   AppError hierarchy + handlers
│   └── pagination.py   Page / PageParams
├── db/
│   ├── base.py         Declarative Base + mixins
│   └── session.py      async engine + get_db()
├── models/             SQLAlchemy ORM classes
├── schemas/            Pydantic DTOs
├── services/           Business logic
├── integrations/       Payme, MinIO, Meili, SMTP
├── tasks/              Celery jobs
├── locale/             email templates / i18n strings
└── scripts/            seed.py, create_superadmin.py
```

## Migrations

```bash
make makemigration m="add users table"
make migrate
```

## Environment

All settings come from the root `.env` (copy of `.env.example`). The container
reads it via `env_file:` in `docker-compose.yml`.
