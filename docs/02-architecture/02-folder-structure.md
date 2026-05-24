# 02. Loyiha Papkalar Tuzilmasi (Folder Structure)

> To'liq monorepo strukturasi. Backend, Frontend va infrastruktura bir repo ichida.

---

## 📁 Asosiy struktura

```
monografiya/
│
├── .github/                       # GitHub Actions (CI/CD)
│   └── workflows/
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       └── deploy.yml
│
├── backend/                       # FastAPI loyihasi
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entry point
│   │   ├── config.py              # Sozlamalar (env)
│   │   ├── dependencies.py        # Umumiy dependencies
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # Asosiy router
│   │   │   │   └── endpoints/
│   │   │   │       ├── auth.py
│   │   │   │       ├── users.py
│   │   │   │       ├── books.py
│   │   │   │       ├── categories.py
│   │   │   │       ├── orders.py
│   │   │   │       ├── payments.py
│   │   │   │       ├── reviews.py
│   │   │   │       ├── search.py
│   │   │   │       ├── authors.py
│   │   │   │       ├── admin.py
│   │   │   │       └── upload.py
│   │   │
│   │   ├── core/                  # Asosiy yordamchilar
│   │   │   ├── __init__.py
│   │   │   ├── security.py        # JWT, parol hash
│   │   │   ├── permissions.py     # Rol-based access
│   │   │   ├── exceptions.py      # Custom exceptions
│   │   │   ├── i18n.py            # Tarjima yordamchi
│   │   │   └── pagination.py      # Pagination utility
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # SQLAlchemy Base
│   │   │   ├── session.py         # DB session
│   │   │   └── init_db.py
│   │   │
│   │   ├── models/                # SQLAlchemy modellar
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── category.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   ├── review.py
│   │   │   ├── author_profile.py
│   │   │   ├── withdrawal.py
│   │   │   └── settings.py
│   │   │
│   │   ├── schemas/               # Pydantic schemalar
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── category.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   └── ...
│   │   │
│   │   ├── services/              # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── book_service.py
│   │   │   ├── order_service.py
│   │   │   ├── payment_service.py
│   │   │   ├── email_service.py
│   │   │   ├── search_service.py
│   │   │   ├── storage_service.py # MinIO
│   │   │   └── pdf_service.py     # Watermark, metadata
│   │   │
│   │   ├── integrations/          # Tashqi servislar
│   │   │   ├── __init__.py
│   │   │   ├── payme/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py      # Payme API client
│   │   │   │   ├── webhook.py     # Callback handler
│   │   │   │   └── schemas.py
│   │   │   ├── minio_client.py
│   │   │   ├── meilisearch_client.py
│   │   │   └── smtp_client.py
│   │   │
│   │   ├── tasks/                 # Celery tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── email_tasks.py
│   │   │   ├── pdf_tasks.py
│   │   │   └── analytics_tasks.py
│   │   │
│   │   ├── locale/                # Backend tarjimalari (email)
│   │   │   ├── uz.json
│   │   │   ├── ru.json
│   │   │   └── en.json
│   │   │
│   │   └── scripts/               # Yordamchi skriptlar
│   │       ├── seed.py            # Demo ma'lumotlar
│   │       └── create_superadmin.py
│   │
│   ├── alembic/                   # Migration fayllari
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── tests/                     # Pytest testlari
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_books.py
│   │   └── ...
│   │
│   ├── alembic.ini
│   ├── pyproject.toml             # yoki requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   └── README.md
│
├── frontend/                      # Nuxt 3 + Vue 3
│   ├── assets/
│   │   ├── css/
│   │   │   └── main.css           # Tailwind imports
│   │   ├── images/
│   │   └── fonts/                 # Inter, Lora shriftlari
│   │
│   ├── components/
│   │   ├── ui/                    # Asosiy UI komponentlar
│   │   │   ├── Button.vue
│   │   │   ├── Input.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Card.vue
│   │   │   ├── Badge.vue
│   │   │   ├── Spinner.vue
│   │   │   └── Toast.vue
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.vue
│   │   │   ├── Footer.vue
│   │   │   ├── Sidebar.vue
│   │   │   ├── LanguageSwitcher.vue
│   │   │   ├── ThemeToggle.vue
│   │   │   └── MobileMenu.vue
│   │   │
│   │   ├── book/
│   │   │   ├── BookCard.vue       # Katalog uchun karta
│   │   │   ├── BookDetail.vue
│   │   │   ├── BookCover.vue
│   │   │   ├── BookRating.vue
│   │   │   └── BookFilters.vue
│   │   │
│   │   ├── auth/
│   │   │   ├── LoginForm.vue
│   │   │   ├── RegisterForm.vue
│   │   │   └── ForgotPasswordForm.vue
│   │   │
│   │   ├── account/
│   │   │   ├── LibraryItem.vue
│   │   │   ├── OrderItem.vue
│   │   │   └── ReviewForm.vue
│   │   │
│   │   ├── author/
│   │   │   ├── BookForm.vue       # Kitob qo'shish/tahrir
│   │   │   ├── SalesChart.vue
│   │   │   └── BalanceCard.vue
│   │   │
│   │   ├── admin/
│   │   │   ├── ModerationCard.vue
│   │   │   ├── StatsCard.vue
│   │   │   └── UserTable.vue
│   │   │
│   │   └── seo/
│   │       ├── SeoHead.vue        # vue-meta wrapper
│   │       └── BreadCrumb.vue
│   │
│   ├── composables/               # Vue composables
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   ├── useCart.ts
│   │   ├── useTheme.ts
│   │   ├── useSeo.ts
│   │   └── useToast.ts
│   │
│   ├── layouts/
│   │   ├── default.vue            # Ommaviy sahifalar
│   │   ├── auth.vue               # Login/register
│   │   ├── account.vue            # O'quvchi kabineti
│   │   ├── author.vue             # Muallif kabineti
│   │   └── admin.vue              # Admin paneli
│   │
│   ├── pages/                     # Nuxt avto-routing
│   │   ├── index.vue              # /
│   │   ├── books/
│   │   │   ├── index.vue          # /books
│   │   │   └── [slug].vue         # /books/[slug]
│   │   ├── category/
│   │   │   └── [slug].vue
│   │   ├── authors/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── search.vue
│   │   ├── blog/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── about.vue
│   │   ├── contact.vue
│   │   ├── faq.vue
│   │   ├── terms.vue
│   │   ├── privacy.vue
│   │   │
│   │   ├── auth/
│   │   │   ├── login.vue
│   │   │   ├── register.vue
│   │   │   ├── forgot-password.vue
│   │   │   └── reset-password.vue
│   │   │
│   │   ├── account/
│   │   │   ├── index.vue
│   │   │   ├── library.vue
│   │   │   ├── favorites.vue
│   │   │   ├── orders/
│   │   │   │   ├── index.vue
│   │   │   │   └── [id].vue
│   │   │   ├── profile.vue
│   │   │   └── settings.vue
│   │   │
│   │   ├── author/
│   │   │   ├── index.vue
│   │   │   ├── books/
│   │   │   │   ├── index.vue
│   │   │   │   ├── new.vue
│   │   │   │   └── [id]/
│   │   │   │       └── edit.vue
│   │   │   ├── sales.vue
│   │   │   ├── balance.vue
│   │   │   ├── withdrawals.vue
│   │   │   └── profile.vue
│   │   │
│   │   ├── admin/
│   │   │   ├── index.vue
│   │   │   ├── moderation.vue
│   │   │   ├── books/
│   │   │   ├── users/
│   │   │   ├── authors/
│   │   │   ├── orders/
│   │   │   ├── payments/
│   │   │   ├── analytics.vue
│   │   │   ├── admins.vue
│   │   │   ├── withdrawals.vue
│   │   │   ├── categories.vue
│   │   │   └── settings/
│   │   │
│   │   ├── cart.vue
│   │   ├── checkout.vue
│   │   └── payment/
│   │       ├── success.vue
│   │       ├── failed.vue
│   │       └── cancelled.vue
│   │
│   ├── middleware/
│   │   ├── auth.ts                # Autentifikatsiya tekshirish
│   │   ├── guest.ts               # Faqat mehmonlar uchun
│   │   ├── author.ts              # Muallif huquqi
│   │   └── admin.ts               # Admin huquqi
│   │
│   ├── plugins/
│   │   ├── api.ts                 # Axios instance
│   │   ├── i18n.ts
│   │   └── toast.ts
│   │
│   ├── stores/                    # Pinia
│   │   ├── auth.ts
│   │   ├── cart.ts
│   │   ├── books.ts
│   │   └── ui.ts                  # Theme, language
│   │
│   ├── locales/                   # i18n tarjima fayllari
│   │   ├── uz.json
│   │   ├── ru.json
│   │   └── en.json
│   │
│   ├── server/                    # Nuxt server middleware
│   │   ├── api/
│   │   │   └── sitemap.xml.ts     # Dinamik sitemap
│   │   └── middleware/
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── robots.txt
│   │   ├── og-default.jpg
│   │   └── images/
│   │
│   ├── types/                     # TypeScript turlari
│   │   ├── api.ts
│   │   ├── book.ts
│   │   ├── user.ts
│   │   └── order.ts
│   │
│   ├── utils/                     # Yordamchi funksiyalar
│   │   ├── formatPrice.ts
│   │   ├── formatDate.ts
│   │   └── slug.ts
│   │
│   ├── nuxt.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── package.json
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   └── README.md
│
├── nginx/                         # Nginx konfiguratsiyalari
│   ├── nginx.conf
│   ├── conf.d/
│   │   ├── default.conf
│   │   └── ssl.conf
│   └── Dockerfile
│
├── docker/                        # Qo'shimcha Docker fayllari
│   ├── postgres/
│   │   └── init.sql               # Boshlang'ich SQL
│   └── certbot/
│       └── renew.sh
│
├── docs/                          # Markdown hujjatlar (shu papka!)
│   ├── 01-overview/
│   ├── 02-architecture/
│   ├── 03-backend/
│   ├── 04-frontend/
│   ├── 05-database/
│   ├── 06-payment/
│   ├── 07-deployment/
│   ├── 08-design/
│   ├── 09-seo/
│   ├── 10-roadmap/
│   └── README.md
│
├── scripts/                       # Loyiha skriptlari
│   ├── setup.sh                   # Birinchi marta sozlash
│   ├── backup.sh                  # DB backup
│   └── deploy.sh                  # Production deploy
│
├── .env.example                   # Umumiy environment
├── .gitignore
├── docker-compose.yml             # Development
├── docker-compose.prod.yml        # Production
├── Makefile                       # Tez-tez ishlatiladigan buyruqlar
├── LICENSE
└── README.md
```

---

## 📝 Asosiy fayllarning vazifasi

### `docker-compose.yml`
Development uchun barcha servislar:
- backend
- frontend
- postgres
- redis
- minio
- meilisearch
- celery_worker
- celery_beat

### `Makefile`
Tez-tez ishlatiladigan buyruqlar:
```makefile
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

backup:
	./scripts/backup.sh
```

---

## 🎨 Frontend papka tushuntirishlari

| Papka | Vazifasi |
|-------|----------|
| `components/` | Qayta ishlatiladigan komponentlar |
| `composables/` | Vue 3 composable funksiyalar |
| `layouts/` | Sahifa shablonlari |
| `pages/` | Nuxt auto-routing |
| `middleware/` | Route'larni himoya qilish |
| `stores/` | Pinia state management |
| `plugins/` | Nuxt plugin'lar |
| `locales/` | Tarjima fayllari |
| `server/` | Server-side kod (SSR) |
| `public/` | Statik fayllar |
| `types/` | TypeScript turlari |

---

## 🐍 Backend papka tushuntirishlari

| Papka | Vazifasi |
|-------|----------|
| `api/` | FastAPI routerlar va endpointlar |
| `core/` | Asosiy yordamchi modullar |
| `db/` | Database setup |
| `models/` | SQLAlchemy modellar (jadvallar) |
| `schemas/` | Pydantic schemalar (DTO) |
| `services/` | Biznes mantiq |
| `integrations/` | Tashqi servislar (Payme, MinIO) |
| `tasks/` | Celery tasklari |
| `alembic/` | DB migration |
| `tests/` | Avtomatik testlar |

---

## 🔑 Asosiy konfiguratsiya fayllari

### `.env.example` (umumiy)
```bash
# Backend
DATABASE_URL=postgresql://user:pass@postgres:5432/monografiya
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your-key
MINIO_SECRET_KEY=your-secret
MINIO_BUCKET=monografiya

# Meilisearch
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_KEY=your-key

# Payme
PAYME_MERCHANT_ID=your-merchant-id
PAYME_SECRET_KEY=your-payme-secret
PAYME_ENDPOINT=https://checkout.paycom.uz/api

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@monografiya.com
SMTP_PASSWORD=your-password

# Frontend
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
NUXT_PUBLIC_SITE_URL=https://monografiya.com
```

---

**Keyingi qadam:** [`03-tech-stack.md`](./03-tech-stack.md) — Texnologiyalar va ularni tanlash sabablari.
