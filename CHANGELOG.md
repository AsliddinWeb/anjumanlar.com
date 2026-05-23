# Changelog

Loyiha phase'lari bo'yicha jamlangan tarix. Har bir bo'limning oxirida
asosiy commit hash'i ko'rsatilgan — to'liq diff'ni GitHub'da o'sha
commit'dan ko'rishingiz mumkin.

Sana formati ISO 8601 (YYYY-MM-DD), versiya hozircha yo'q —
launch'gacha asosiy daraxt `main` ustida ishlaymiz.

## Unreleased

- Phase 7.6 (Payme sandbox e2e) — qo'lda real merchant credentials
  bilan tekshirish; backend kodi tayyor (Phase 4.4).
- Frontend i18n v9 migratsiyasi `@nuxtjs/seo` paketini qo'shish uchun
  zarur — post-launch Phase 8 ga rejalashtirilgan.

## 2026-05-23 — Phase 7 (launch readiness) [`42c5f36`, `574dc7a`, `4fcb597`, `500be99`]

- **7.1 — Blog tizimi**: `BlogPost` model + admin CRUD + public
  `/blog`, `/blog/[slug]` (3 lokalda). Sitemap'ga blog URL'lar qo'shildi.
  9 ta yangi test. Phase 3 placeholder almashtirildi.
- **7.2 — Sentry monitoring**: backend `sentry-sdk[fastapi]`, frontend
  `@sentry/vue` (lazy-loaded). DSN bo'sh bo'lganda no-op.
- **7.3 — Backup + restore**: `scripts/backup.sh` (`pg_dump` + MinIO
  tarball, 30-kunlik retention) va `scripts/restore.sh` (idempotent,
  `--dry-run`, `--force`). `make prod-backup` / `prod-restore` target'lari.
- **7.4 — Email kengaytirish**: 6 ta yangi template (uz/ru/en × 6 = 18
  fayl) — `order_paid`, `book_approved`, `book_rejected`,
  `withdrawal_{requested,completed,rejected}`. Drive-by fix:
  `library_grant` mavzusi `SUBJECTS` katalogiga qo'shildi.
- **7.5 — A11y polish**: `:focus-visible` ring, skip-to-content link,
  `useEscape` composable + 7 ta modal/drawer Esc bilan yopiladi.

## 2026-05-23 — Phase 6 (SEO + sitemap) [`ed25f4f`]

Variant B: Nuxt 3.15 + i18n v8 + unhead v1 stack saqlandi, SEO qo'lda
yozildi (`@nuxtjs/seo` paketi kelajakka qoldirilgan).

- `useSiteSeo` composable — OG, Twitter, canonical, hreflang har sahifada.
- `useStructuredData` — Organization (home), Book, Person,
  BreadcrumbList JSON-LD generatorlari.
- Dinamik `/sitemap.xml` (66 URL: 5 static × 3 lokal + kitoblar +
  kategoriyalar + mualliflar).
- `/robots.txt` — admin/account/auth/checkout/cart/search disallowed.
- 11 ta public sahifada SEO meta + hreflang ulandi (`/search` va 404 noindex).

## 2026-05-22 — Phase 5 (admin panel) [`fb5647a`, `805c582`]

- **5.1 — Admin layout + middleware**: sidebar (desktop) + drawer
  (mobile) layout, `admin` route middleware, `/admin` index.
- **5.2 — Kitob moderatsiya**: `/admin/books` pending queue +
  approve/reject (reason bilan).
- **5.3 — Sharh moderatsiyasi**: `/admin/reviews` pending queue.
- **5.4 — Kategoriya CRUD**: `/admin/categories` jadval + 3 lokal
  modal (slug, name, icon, parent, sort).
- **5.5 — Foydalanuvchi boshqaruvi** (yangi backend): list + role +
  status mutations, self-mutation + superadmin protection.
- **5.6 — Withdrawal admin UI**: status filter + 4 ta action modal
  (approve, processing, complete, reject).
- **5.7 — KPI dashboard** (yangi backend): `stats_service.snapshot`,
  action item cards + 6 ta KPI card.
- **5.8 — Audit log**: list endpoint + filter; INET → str pydantic fix.
- **5.9 — Bootstrap script**: `create_admin.py` idempotent superadmin
  yaratish/promote qilish CLI'si.

11 yangi admin user testi, 6 ta stats, 5 ta audit + service-level
testlar. To'liq suite 250+ green.

## 2026-05-22 — Deploy infra [`a6b3c49`]

- `docker-compose.prod.yml` — host port'lar `127.0.0.1` ga bog'langan,
  nginx container 80/443 dan tashqarida.
- `backend/Dockerfile.prod` — uvicorn 4 worker, no-reload,
  `--forwarded-allow-ips=*`.
- `frontend/Dockerfile.prod` — multi-stage build, `.output/server` ni
  `node` user ostida xizmat qilish.
- `nginx/conf.d/anjumanlar.com.conf` — HTTP-only bloklar (certbot SSL
  qo'shadi), `files.anjumanlar.com` subdomain MinIO presigned URL uchun.
- `.env.prod.example`, `scripts/deploy.sh`, `DEPLOY.md`, Makefile
  `prod-*` target'lari.

## 2026-05-21 — Phase 4 (to'lov + library + withdrawal) [`e46137f`]

- **DB**: Order/OrderItem/Payment/UserLibrary/Withdrawal + 4 enum,
  `orders_seq` sequence, alembic.
- **Servislar**: `order_service` (state machine + expire), Payme
  `PaymeMerchant` (6 JSON-RPC method, idempotent), `library_service`
  (grant_order: balance + watermark + email, re-entrant),
  `withdrawal_service` (state machine, pending/available bookkeeping).
- **API**: `/orders`, `/payments/payme/{webhook,checkout/{id}}`,
  `/libraries/me[/{book_id}/download]` (presigned MinIO),
  `/authors/me/{balance,withdrawals}`, `/admin/withdrawals/{id}/*`.
- **Frontend**: cart (localStorage) + wishlist (Pinia), `/cart`
  checkout, `/checkout/{success,failed}`, `/account/{library,orders,
  wishlist,balance,withdrawals}`. Header'da cart count badge.
- **Celery beat**: `orders.expire_pending` har daqiqada pending
  orderlarni `expired` qiladi.
- 48 yangi pytest test.

## 2026-05-21 — Phase 3 (public sahifalar) [`80a90e8`]

- Bosh sahifa, katalog (URL-sync filterlar + sort + paginatsiya),
  kitob detali (sharhlar + similar + demo viewer), kategoriya,
  mualliflar ro'yxati + profil, qidiruv, about, blog placeholder,
  legal sahifalar.
- 11 ta UI primitiv (`Ui*`), 8 ta book/author komponent.
- Mobile drawer + footer 4-ustun + 404 catch-all.

## 2026-05-21 — Phase 2 (books + uploads + search) [`63af70f`]

- Book lifecycle (draft → pending → approved/rejected), author
  profile, kategoriya CRUD, sharhlar.
- MinIO file upload (cover via Pillow, PDF via pypdf), Celery demo
  PDF generation, watermark task tayyorlandi.
- Meilisearch integratsiyasi (`/search?q=...`).

## 2026-05-21 — Phase 1 (auth + RBAC) [`cc5bc62`]

- JWT access (30 daq) + opaque refresh token (DB-backed, rotatable).
- Email verify + password reset, audit log (13 ta action), rate
  limiting login/register'da.
- bcrypt parol hashlash, role hierarchy (reader < author < admin <
  superadmin).

## Phase 0 (skeleton)

- Docker Compose stack: postgres, redis, minio, meilisearch, mailhog,
  backend, frontend, celery worker + beat. Port'lar 8300+ dan.
- FastAPI + Nuxt 3 + Alembic + Tailwind skeletoni.
- `make help` orqali boshqarish.
