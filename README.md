# Anjumanlar.com

> Mualliflar uchun monografiyalarni yuklash va sotish platformasi. 3 tilli
> (uz/ru/en), kunduzgi/tungi rejim, Payme.uz to'lov, admin panel, SEO va
> Sentry monitoring bilan Docker'da yetkaziladi.

**Holati:** feature-complete (Phase 0–7), production deploy uchun
tayyor. Birinchi launch oldidan [LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md)
ga rioya qiling.

## Tech stack

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.0 async + Alembic |
| Frontend | Nuxt 3.15 (Vue 3 + TypeScript) + Tailwind CSS + Pinia + i18n v8 |
| DB | PostgreSQL 16 |
| Cache / queue | Redis 7 + Celery (worker + beat) |
| Files | MinIO (S3-mos) |
| Search | Meilisearch 1.6 |
| Payment | Payme.uz (JSON-RPC webhook) |
| Email | SMTP (dev: MailHog, prod: Brevo/Resend/…) |
| Monitoring | Sentry (backend + frontend) |
| Proxy | Nginx + Let's Encrypt certbot |

To'liq hujjat: [`docs/`](./docs/README.md) — 31 ta `.md` fayl, 10 ta bo'lim.
Deploy yo'riqnomasi: [DEPLOY.md](./DEPLOY.md).
Tarix: [CHANGELOG.md](./CHANGELOG.md).

## Port layout (8300+)

Bir necha mahalliy loyihalarni parallel ishlatish uchun barcha portlar
**8300 dan boshlanadi**.

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
| Nginx (production) | **80/443** | <https://anjumanlar.com> |

## Quick start (dev)

```bash
# 1. Clone
git clone https://github.com/AsliddinWeb/anjumanlar.com.git anjumanlar
cd anjumanlar

# 2. Environment
make env                  # copies .env.example -> .env
# Edit .env, set strong passwords + JWT_SECRET_KEY

# 3. Start every dev service
make up

# 4. Migrations + seed (first run only)
make migrate
make seed

# 5. Open in the browser
# Frontend:    http://localhost:8308
# Backend:     http://localhost:8307/docs
# MinIO:       http://localhost:8303
# MailHog:     http://localhost:8306
```

Boshqa buyruqlar: `make help`.

## What's built

### Public site
- Bosh sahifa, katalog (URL-sync filterlar + sort + paginatsiya)
- Kitob detali — sharhlar, demo PDF viewer, similar books, JSON-LD
- Kategoriya, mualliflar ro'yxati va profil sahifalari
- Qidiruv (Meilisearch backed) — backend `/api/v1/search`
- About, blog (admin tomonidan boshqariladigan maqolalar), legal sahifalar
- Mobile drawer + skip-to-content link + `:focus-visible` rings

### Auth
- Register + email verify + login + parol tiklash + logout-all
- JWT access + opaque refresh token (DB-backed, rotatable)
- bcrypt parol hashlash, rate limit (login/register)
- Audit log: 13 ta action turi

### Foydalanuvchi
- Sevimlilar (wishlist), savat (localStorage), buyurtmalar tarixi
- Payme checkout flow (sandbox/production)
- Sotib olishdan keyin watermarked PDF kutubxonadan yuklab olish
- Hisob profili va parolni o'zgartirish

### Muallif
- Muallif profili yaratish (`/authors/me` orqali "become author")
- Kitob yuklash (cover + PDF), draft → submit → moderation oqimi
- Daromad balansi, sotuvlar, pul yechish so'rovlari
- Email notifications: kitob tasdiqlandi/rad etildi, withdrawal status

### Admin
- KPI dashboard (foydalanuvchilar, kitoblar, daromad, ochiq so'rovlar)
- Kitob moderatsiyasi (approve + reject reason bilan)
- Sharh moderatsiyasi, kategoriya CRUD, blog post CRUD
- Foydalanuvchi boshqaruvi (rol/status, block/unblock)
- Withdrawal workflow: requested → approved → processing → completed
- Audit log feed (user/action filter)
- Superadmin bootstrap script (`make prod-create-admin`)

### SEO + observability
- `useSiteSeo` har sahifada — OG, Twitter, canonical, hreflang (uz/ru/en)
- JSON-LD: Organization (home), Book, Person, BlogPosting, BreadcrumbList
- Dinamik `/sitemap.xml` (kitoblar + mualliflar + kategoriyalar + blog)
- `/robots.txt` (admin/account/auth/checkout disallowed)
- Sentry: backend (FastAPI + Starlette + SQLAlchemy integrations) va
  frontend (`@sentry/vue` lazy-loaded). DSN bo'sh bo'lsa no-op.

### Backup
- `scripts/backup.sh` — `pg_dump` (custom format) + MinIO volume tarball,
  30-kunlik retention
- `scripts/restore.sh` — idempotent restore (`--dry-run`, `--force`)
- `make prod-backup` / `make prod-restore BACKUP=…`

## Folder structure

```
anjumanlar/
├── backend/        FastAPI app + Alembic + Celery + tests
├── frontend/       Nuxt 3 + Tailwind + Pinia + i18n
├── nginx/          Reverse proxy config (anjumanlar.com.conf)
├── docker/         postgres init, certbot, minio setup
├── docs/           Project documentation (31 md files)
├── scripts/        deploy.sh, backup.sh, restore.sh
├── .env.example    Dev environment template
├── .env.prod.example  Production environment template
├── docker-compose.yml       (dev)
├── docker-compose.prod.yml  (production)
├── DEPLOY.md       Production deploy + Sentry + backup guide
├── LAUNCH_CHECKLIST.md  Go-live checklist
├── CHANGELOG.md    Phase-by-phase history
└── Makefile
```

## Development phases

| Phase | Mazmuni | Holati |
|-------|---------|--------|
| 0 | Docker skeleton, port 8300+ | ✅ |
| 1 | Auth + RBAC + audit log | ✅ |
| 2 | Books CRUD + uploads + Meilisearch + reviews | ✅ |
| 3 | Public sayt — barcha foydalanuvchi sahifalari | ✅ |
| 4 | To'lov + cart + library + withdrawal | ✅ |
| 5 | Admin panel (moderation + users + KPI + audit) | ✅ |
| 6 | SEO — meta + sitemap + JSON-LD + hreflang | ✅ |
| 7 | Launch readiness — blog, Sentry, backup, a11y, docs | ✅ |

Roadmap: [`docs/10-roadmap/01-development-phases.md`](./docs/10-roadmap/01-development-phases.md).

## Production deploy

To'liq yo'riqnoma: [DEPLOY.md](./DEPLOY.md). Qisqacha:

```bash
# Server'da
cd /opt && sudo git clone https://github.com/AsliddinWeb/anjumanlar.com.git
cd anjumanlar.com
cp .env.prod.example .env  # to'ldiring: secret keys, SMTP, Sentry, Payme
make prod-build
make prod-up
make prod-migrate
make prod-seed                  # 10 ta kategoriya
make prod-create-admin EMAIL=you@anjumanlar.com PASSWORD='Strong!' NAME='Admin'

# SSL (certbot Docker bilan)
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot --webroot-path=/var/www/certbot \
    --email you@anjumanlar.com --agree-tos --no-eff-email \
    -d anjumanlar.com -d www.anjumanlar.com -d files.anjumanlar.com
```

Launch oldidan: [LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md).

## Tests

```bash
make test              # backend pytest (280+ test)
make lint              # ruff + eslint
docker compose exec frontend pnpm typecheck
```

Backend test suite Phase 7.4 holatida — **280/280 yashil**.

## Documentation

- [`docs/README.md`](./docs/README.md) — barcha 31 ta hujjat indeksi
- [`docs/01-overview/`](./docs/01-overview/) — loyiha, foydalanuvchi rollari, sahifalar
- [`docs/02-architecture/`](./docs/02-architecture/) — arxitektura, papka tuzilmasi
- [`docs/03-backend/`](./docs/03-backend/) — FastAPI, endpoints, auth, fayl yuklash
- [`docs/04-frontend/`](./docs/04-frontend/) — Nuxt, sahifalar, komponentlar, i18n
- [`docs/05-database/`](./docs/05-database/) — schema, migrations, seed
- [`docs/06-payment/`](./docs/06-payment/) — Payme integratsiyasi
- [`docs/07-deployment/`](./docs/07-deployment/) — Docker, Nginx, SSL
- [`docs/08-design/`](./docs/08-design/) — design system
- [`docs/09-seo/`](./docs/09-seo/) — SEO strategiyasi
- [`docs/10-roadmap/`](./docs/10-roadmap/) — phase'lar va MVP checklist

## Troubleshooting

| Belgi | Yechim |
|-------|--------|
| `make up` xato — port band | Boshqa loyiha `83xx` portda. To'xtating yoki `.env`'da o'zgartiring. |
| Frontend `t('site.title')` qatorida | Locale fayllari `frontend/locales/` da bo'lishi kerak (`@nuxtjs/i18n@8`). |
| `/api/v1/ready` `db: fail` qaytaradi | Postgres hali tayyor emas. `make logs s=postgres` orqali kuting. |
| Backend o'zgarishlari reload qilmayapti | `uvicorn --reload` `/app`ni kuzatadi; bind-mount `./backend:/app` ekanini tekshiring. |
| `alembic upgrade head` UUID xato | Postgres init o'tkazib yuborilgan. `make clean && make up`. |
| Sentry ulanmadi | DSN bo'sh — `.env`da `SENTRY_DSN=` va `NUXT_PUBLIC_SENTRY_DSN=` ni to'ldiring. |
| Email kelmadi | Dev'da MailHog UI <http://localhost:8306> tekshiring. Prod'da SMTP keylar to'g'rimi. |

## Contributing

Branch nomi, commit format, test buyruqlari uchun
[CONTRIBUTING.md](./CONTRIBUTING.md) ga qarang. Claude Code agentlari:
[CLAUDE.md](./CLAUDE.md) ni avval o'qing.

## License

Proprietary — qarang [LICENSE](./LICENSE).
