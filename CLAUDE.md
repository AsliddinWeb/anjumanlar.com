# CLAUDE.md — instructions for Claude Code

These notes orient Claude Code (or any AI pair-programmer) before touching this
repository.

## What this project is

`anjumanlar.com` — a marketplace where authors upload monographs (PDF/EPUB
scientific books) and readers buy them. Payments go through Payme.uz; the UI
ships in three languages (uz/ru/en) with light/dark mode.

Tech stack: FastAPI + SQLAlchemy 2.0 async (backend), Nuxt 3 + Tailwind +
@nuxtjs/i18n v8 (frontend), Postgres 16, Redis 7, MinIO, Meilisearch, Celery,
Docker Compose for development, Nginx + Let's Encrypt in production.

Source of truth for product and architecture: [`docs/`](./docs/README.md) —
31 markdown files organised under `01-overview/` through `10-roadmap/`. The
shipping plan lives in `docs/10-roadmap/01-development-phases.md`; the
sub-phase breakdown for Phase 0 was authored interactively (see the
conversation that produced this commit).

## Port layout (host machine)

Every service is published on a port in the **8300+** range so several
projects can run in parallel:

| Service | Host | Container |
|---------|------|-----------|
| PostgreSQL | 8300 | 5432 |
| Redis | 8301 | 6379 |
| MinIO API | 8302 | 9000 |
| MinIO Console | 8303 | 9001 |
| Meilisearch | 8304 | 7700 |
| MailHog SMTP | 8305 | 1025 |
| MailHog UI | 8306 | 8025 |
| Backend (FastAPI) | 8307 | 8000 |
| Frontend (Nuxt) | 8308 | 3000 |
| Nginx (prod only) | 8309 | 80 |
| Flower (reserved) | 8310 | 5555 |

Inside Docker, services talk to each other on the **internal** ports
(`postgres:5432`, `redis:6379`, …). From the host machine use the 8300+ port
(`localhost:8300`, etc.). The same `.env` file feeds both — container code
sees `postgres:5432`, host tools see `localhost:8300`.

## Common commands

All driven from the repo root via the `Makefile`:

```bash
make help            # list targets
make up              # start every service
make down            # stop
make logs s=backend  # tail one service
make migrate         # alembic upgrade head
make seed            # populate demo data (added in Phase 1)
make test            # backend pytest
make lint            # ruff + eslint
make format          # ruff format + prettier
make shell-backend   # bash in backend container
make shell-db        # psql
```

## Editing rules

1. **Don't break the port layout.** Hardcoding `localhost:5432` or `8000` in
   any code or doc is wrong — read from `.env` / `runtimeConfig`.
2. **Don't introduce SEO modules yet.** `@nuxtjs/seo`, `@nuxtjs/sitemap` and
   `@nuxtjs/robots` were intentionally left out: their `unhead@2.x` clashes
   with `@nuxtjs/i18n@8`. They land in Phase 6.
3. **Pin Nuxt to `~3.15`.** Bumping to 3.16+ pulls unhead 2 and breaks i18n
   v8. The pnpm override (`unhead: ^1.11.0`) enforces this.
4. **Frontend deps are containerised.** The host has no `node_modules`, so
   VS Code's "package not installed" hints in `package.json` are expected —
   ignore them or attach VS Code to the running container (Dev Containers
   extension).
5. **Backend deps are containerised.** Same story for Python — the venv lives
   in `/opt/venv` inside the backend image. Use `make shell-backend` for an
   interactive REPL.
6. **No comments unless the why is non-obvious.** Well-named identifiers do
   most of the documentation work; PR descriptions cover the rest.
7. **One sub-phase at a time.** Don't add Phase 1 endpoints to the Phase 0
   skeleton — keep skeleton commits scoped.

## Where things live

```
backend/app/
  api/v1/endpoints/   # one router per resource (auth, books, …)
  core/               # cross-cutting (exceptions, pagination, security)
  db/                 # session + Base + mixins
  models/             # SQLAlchemy ORM
  schemas/            # Pydantic DTOs
  services/           # business logic
  integrations/       # payme, minio, meilisearch, smtp
  tasks/              # celery jobs

frontend/
  components/{layout,ui,book,…}/   # auto-imported without folder prefix
  composables/                     # useApi, useAuth (Phase 1+)
  layouts/                         # default, auth, account, author, admin
  pages/                           # nuxt auto-routing
  locales/{uz,ru,en}.json          # vue-i18n v8 lazy-loaded
  stores/                          # pinia
  middleware/                      # auth, guest, author, admin
  assets/css/main.css              # CSS variables for light/dark
```

## When in doubt

Read the relevant doc under `docs/` first. The MVP checklist
(`docs/10-roadmap/02-mvp-checklist.md`) lists every endpoint, page and
feature with the granularity needed to scope an issue.
