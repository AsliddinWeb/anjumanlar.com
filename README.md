# Anjumanlar.com

> Mualliflar uchun monografiyalarni yuklash va sotish platformasi. 3 tilli (uz/ru/en), kunduzgi/tungi rejim, Payme.uz to'lov, Docker bilan deploy.

## Tech stack

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | FastAPI (Python 3.12+) + SQLAlchemy 2.0 async |
| Frontend | Nuxt 3 (Vue 3 + TypeScript) + Tailwind CSS |
| DB | PostgreSQL 16 |
| Cache / queue | Redis 7 + Celery |
| Files | MinIO (S3-mos) |
| Search | Meilisearch |
| Payment | Payme.uz |
| Proxy | Nginx + Let's Encrypt |

To'liq hujjat: [`docs/`](./docs/README.md) — 31 ta `.md` fayl, 10 ta bo'lim.

## Port layout (8300+)

Bir necha mahalliy loyihalarni parallel ishlatish uchun barcha portlar **8300 dan boshlanadi**.

| Servis | Host port | URL |
|--------|-----------|-----|
| PostgreSQL | **8300** | `localhost:8300` |
| Redis | **8301** | `localhost:8301` |
| MinIO API | **8302** | `localhost:8302` |
| MinIO Console | **8303** | <http://localhost:8303> |
| Meilisearch | **8304** | <http://localhost:8304> |
| MailHog SMTP | **8305** | `localhost:8305` |
| MailHog UI | **8306** | <http://localhost:8306> |
| Backend (FastAPI) | **8307** | <http://localhost:8307/docs> |
| Frontend (Nuxt) | **8308** | <http://localhost:8308> |
| Nginx (production) | **8309** | <http://localhost:8309> |
| Flower (Celery) | **8310** | <http://localhost:8310> |

## Quick start

```bash
# 1. Clone
git clone <repo-url> anjumanlar
cd anjumanlar

# 2. Environment
make env                  # copies .env.example -> .env
# Edit .env, set strong passwords + JWT_SECRET_KEY

# 3. Start dev services
make up

# 4. Run migrations + seed (first run only)
make migrate
make seed

# 5. Open in browser
# Frontend:    http://localhost:8308
# Backend:     http://localhost:8307/docs
# MinIO:       http://localhost:8303
# MailHog:     http://localhost:8306
```

Boshqa buyruqlar uchun: `make help`

## Folder structure

```
anjumanlar/
├── backend/        FastAPI app + Alembic + Celery
├── frontend/       Nuxt 3 + Tailwind
├── nginx/          Reverse proxy config
├── docker/         postgres init scripts, certbot, minio
├── docs/           Project documentation (31 md files)
├── scripts/        setup.sh, backup.sh, deploy.sh
├── .github/        CI/CD workflows
├── .env.example    Environment template
├── docker-compose.yml
├── docker-compose.prod.yml
└── Makefile
```

Batafsil: [`docs/02-architecture/02-folder-structure.md`](./docs/02-architecture/02-folder-structure.md)

## Development phases

Loyiha 7 ta phase'ga bo'lingan (`docs/10-roadmap/01-development-phases.md`):

- **Phase 0** — Tayyorgarlik, arxitektura, Docker skeleton (1-2 hafta)
- **Phase 1** — Backend core + Auth (2 hafta)
- **Phase 2** — Kitob CRUD + Qidiruv + Upload (2 hafta)
- **Phase 3** — Frontend public sahifalar (2 hafta)
- **Phase 4** — Cart, Checkout, Payme to'lov (1 hafta)
- **Phase 5** — Admin panel + Author kabineti (1-2 hafta)
- **Phase 6** — SEO + Performance + Deploy (1-2 hafta)

## Documentation

- [`docs/README.md`](./docs/README.md) — Index of all 31 doc files
- [`docs/01-overview/`](./docs/01-overview/) — Project summary, user roles, pages, features
- [`docs/02-architecture/`](./docs/02-architecture/) — System architecture, folder structure, tech stack
- [`docs/03-backend/`](./docs/03-backend/) — FastAPI setup, endpoints, auth, file upload
- [`docs/04-frontend/`](./docs/04-frontend/) — Nuxt setup, pages, components, i18n, theme
- [`docs/05-database/`](./docs/05-database/) — Schema, migrations, seed
- [`docs/06-payment/`](./docs/06-payment/) — Payme integration, payment flow
- [`docs/07-deployment/`](./docs/07-deployment/) — Docker, Nginx, SSL, production checklist
- [`docs/08-design/`](./docs/08-design/) — Design system, UI guidelines
- [`docs/09-seo/`](./docs/09-seo/) — SEO strategy, meta tags, sitemap
- [`docs/10-roadmap/`](./docs/10-roadmap/) — Development phases, MVP checklist

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `make up` fails — port already in use | Another project occupies an `83xx` port. Stop it or remap in `.env`. |
| Frontend page shows raw `t('site.title')` | Locale files moved — they must live under `frontend/locales/`, not `i18n/locales/` (we use `@nuxtjs/i18n@8`). |
| `/api/v1/ready` returns `db: fail` | Postgres still warming up. `make logs s=postgres`, wait for `database system is ready`. |
| Backend changes don't reload | `uvicorn --reload` watches `/app`; check the bind-mount is `./backend:/app`. |
| MinIO Console 502 | Console is **8303**, S3 API is **8302**. The console only serves UI. |
| `pnpm-lock.yaml` conflicts after merge | Regenerate inside container: `docker compose exec frontend pnpm install --lockfile-only`. |
| `alembic upgrade head` UUID extension error | Postgres missed init. `make clean && make up` to re-run `docker/postgres/init.sql`. |
| Sharp warning on Apple Silicon during build | Cosmetic — the `linux-arm64` binary is missing in the image. Frontend still works; CI runs on amd64. |

More cases in [CONTRIBUTING.md](./CONTRIBUTING.md#troubleshooting).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for branch naming, commit format,
test commands, and PR rules. Claude Code agents: read [CLAUDE.md](./CLAUDE.md)
first.

## License

Proprietary — see [LICENSE](./LICENSE).
