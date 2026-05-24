# Contributing

Thanks for working on Monografiya. This file covers everything you need to
get a clean change merged.

## Prerequisites

- Docker Desktop 24+ (Compose v2)
- Git
- A code editor — VS Code is the assumed default; recommended extensions live
  in `.vscode/extensions.json`

You do **not** need a local Python or Node install: the containers provide
both. If you want IDE autocomplete on the host, run `pnpm install` inside
`frontend/` and `pip install -e ".[dev]"` inside `backend/` against a Python
3.12 venv — they're optional convenience installs.

## First-time setup

```bash
git clone <repo-url> monografiya
cd monografiya
make env        # copies .env.example -> .env
# Edit .env: replace every "change-me-…" value with a real one.
make up         # builds + starts every service
make migrate    # alembic upgrade head (no-op until Phase 1 ships models)
```

Open:

- Frontend (Nuxt SSR): <http://localhost:8308>
- Backend Swagger: <http://localhost:8307/docs>
- MinIO Console: <http://localhost:8303>  (credentials = `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`)
- MailHog UI: <http://localhost:8306>

## Branching & commits

- `main` — protected, deploys to production (post-Phase 6).
- `dev` — integration branch, always green.
- Feature branches: `feature/<phase>-<slug>` (e.g. `feature/1-auth-jwt`).
- Bug fixes: `fix/<slug>`.
- Hot patches: `hotfix/<slug>`.

Commit messages follow Conventional Commits:

```
feat(auth): add JWT refresh-token rotation
fix(books): validate cover MIME type before upload
chore(deps): bump fastapi to 0.115
docs(roadmap): tighten phase 4 acceptance criteria
```

Keep commits small and atomic. Rebase before opening a PR.

## Code style

| Stack | Tool | Command |
|-------|------|---------|
| Python | Ruff (lint + format), mypy strict | `make lint`, `make format` |
| TypeScript / Vue | ESLint (Nuxt flat config), Prettier | `pnpm lint`, `pnpm format` |
| SQL | hand-edit migrations; one `op.*` per logical change | — |
| YAML / JSON / MD | Prettier | `pnpm format` |

CI runs the lint + format check + tests on every PR. Locally:

```bash
make lint        # both backend and frontend
make format      # auto-fix everything
make test        # backend pytest
```

## Tests

- **Backend** — `pytest` against a Postgres + Redis service. Coverage target
  is 60% by end of Phase 6. Place tests under `backend/tests/` mirroring the
  module path being tested. Integration tests must hit a real Postgres, not
  mocks.
- **Frontend** — Vitest for components + composables (lands in Phase 3).
  Playwright E2E for the register → buy → download flow (lands in Phase 6).

## Database migrations

```bash
# Edit models under backend/app/models/, then:
make makemigration m="add books table"
# Review the file under backend/alembic/versions/. Run:
make migrate
# To roll back the last migration during dev:
docker compose exec backend alembic downgrade -1
```

Never edit a migration file once it has been merged to `main` — write a
new one that fixes the previous.

## Adding a frontend page

1. Drop `pages/foo.vue` — Nuxt routes it automatically.
2. Use `useLocalePath('/foo')` for navigation; raw `/foo` skips i18n.
3. Add translation keys for the new page to **all three** `locales/*.json`.
4. If the page needs auth, set `definePageMeta({ middleware: 'auth' })`.

## Pull requests

A PR is mergeable when:

- CI is green (backend + frontend + compose workflows).
- At least one reviewer approves.
- Linked to an issue or phase deliverable.
- The description explains the *why*, not just the *what*.
- No unrelated changes (dependencies, formatting drift). Use a separate PR.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `make up` says ports in use | Another project is on 8300+. Stop it or change `.env` ports. |
| Frontend HMR doesn't reach the browser | Restart `frontend` service; check `vite.server.hmr.clientPort` matches your host port. |
| Backend `/ready` returns `db: fail` | Postgres container not healthy yet — wait 5s or check `make logs s=postgres`. |
| Locales not loading | Files must live under `frontend/locales/` (not `i18n/locales/`); we use `@nuxtjs/i18n@8`. |
| `alembic upgrade head` errors on UUID | `pgcrypto` extension missing — re-run `make clean && make up` to re-init Postgres. |
| MinIO Console returns 502 | The console is on 8303, the S3 API on 8302 — don't swap them. |

## Documentation

The canonical product + architecture spec lives under [`docs/`](./docs/README.md).
When you change anything that affects:

- API surface — update `docs/03-backend/02-api-endpoints.md`.
- Database — update `docs/05-database/01-schema.md` and add a migration.
- Page list — update `docs/01-overview/03-pages-list.md`.

The roadmap (`docs/10-roadmap/`) is the project plan; phase scope changes
require a maintainer's sign-off.
