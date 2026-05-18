# 03. Texnologiyalar To'plami (Tech Stack)

> Har bir texnologiya **nima uchun tanlangani** va **muqobil variantlari** bilan to'liq tushuntiriladi.

---

## 🐍 Backend: FastAPI

### Sabab:
- **Tez** — eng tez Python framework'laridan biri (Node.js, Go bilan raqobat)
- **Async/await** — qutidan tashqari (out of the box)
- **OpenAPI/Swagger** avtomatik generatsiya — `/docs` endpoint avtomatik
- **Pydantic v2** — eng tez validation kutubxonasi
- **Type hints** — IDE yordami, kam xatolik
- **O'rganish oson** — Flask kabi sodda, Django'dan ko'ra moslashuvchan

### Yordamchi kutubxonalar:

| Kutubxona | Vazifasi |
|-----------|----------|
| `fastapi` | Asosiy framework |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy[asyncio]` | ORM |
| `alembic` | Migration |
| `asyncpg` | PostgreSQL async driver |
| `pydantic` | Validation |
| `pydantic-settings` | Sozlamalar |
| `python-jose[cryptography]` | JWT |
| `passlib[bcrypt]` | Parol hash |
| `python-multipart` | Fayl yuklash |
| `celery` | Background tasks |
| `redis` | Redis client |
| `minio` | MinIO client |
| `meilisearch` | Search client |
| `httpx` | HTTP client (Payme uchun) |
| `pillow` | Rasm ishlash |
| `pypdf` | PDF metadata |
| `reportlab` | PDF watermark |
| `email-validator` | Email tekshirish |
| `aiosmtplib` | Email async yuborish |
| `slowapi` | Rate limiting |

---

## 🎨 Frontend: Vue.js 3 + Nuxt 3

### Sabab Vue 3 ni:
- **Engil va tez** — React'ga qaraganda kichik bundle
- **Composition API** — modern, type-safe
- **Single File Components** — HTML, CSS, JS bir faylda
- **O'rganish oson** — boshlovchi uchun React'dan oson

### Sabab Nuxt 3 ni:
- **SSR/SSG** — SEO uchun majburiy
- **Auto routing** — `pages/` papkasidan avtomatik
- **Auto imports** — komponentlar, composables avtomatik import
- **Modul ekotizimi** — boy plugin'lar
- **Nitro server** — serverless ready

### Yordamchi kutubxonalar:

| Kutubxona | Vazifasi |
|-----------|----------|
| `nuxt` | Framework |
| `@nuxtjs/tailwindcss` | Tailwind integration |
| `@nuxtjs/i18n` | Ko'p tillilik |
| `@pinia/nuxt` | State management |
| `@vueuse/nuxt` | Composable utility'lar |
| `@nuxt/image` | Optimized rasmlar |
| `@nuxtjs/seo` | SEO meta teglar |
| `@nuxtjs/sitemap` | Sitemap.xml |
| `@nuxtjs/robots` | robots.txt |
| `@nuxtjs/color-mode` | Tungi rejim |
| `@headlessui/vue` | A11y komponentlar |
| `@heroicons/vue` | Iconlar |
| `chart.js` + `vue-chartjs` | Grafiklar |
| `vue-router` | (Nuxt'da o'rnatilgan) |
| `axios` yoki `ofetch` | HTTP client |
| `vee-validate` + `zod` | Forma validatsiya |
| `dayjs` | Sana formatlash |
| `marked` yoki `markdown-it` | Markdown render |

---

## 💄 Dizayn: Tailwind CSS

### Sabab:
- **Utility-first** — tezroq yozish
- **Optimallashtirilgan** — faqat ishlatilgan classlar bundle'ga kiradi
- **Dark mode qo'llab-quvvatlash** — qutidan
- **Responsive** — `sm:`, `md:`, `lg:` prefikslar
- **Customization** — `tailwind.config.js` orqali to'liq sozlash
- **Plugin ekotizimi** — Typography, Forms, Aspect ratio

### Qo'shimcha:
- **Headless UI** (`@headlessui/vue`) — accessibility'siz UI komponentlari
- **Heroicons** (`@heroicons/vue`) — bepul, ochiq iconlar
- Yoki **Lucide Icons** — yana yaxshi alternativ

---

## 🗄 Ma'lumotlar bazasi: PostgreSQL 16

### Sabab:
- **Ishonchli** — yillar davomida sinalgan
- **JSONB** — ko'p tilli matnlar uchun a'lo (tarjimalar)
- **Full-text search** — qo'shimcha (lekin biz Meilisearch ishlatamiz)
- **Transactions** — to'lov uchun majburiy
- **Backup va replication** — yaxshi yo'lga qo'yilgan
- **Bepul va ochiq kodli**

### MongoDB emas, nima uchun?
- Bizning ma'lumotlar **strukturali** (foydalanuvchi, kitob, buyurtma) — relational uchun mos
- Tranzaksiya kerak (to'lov) — PostgreSQL kuchli
- ACID kafolatlari muhim

---

## ⚡ Redis 7

### Vazifalari:
1. **Sessiya saqlash** — refresh tokenlar
2. **Kesh** — sahifalar, kategoriyalar, top kitoblar
3. **Rate limit** — counter saqlash
4. **Celery broker** — task queue

### Sabab Redis:
- Eng tez in-memory store
- Persistence qo'llab-quvvatlaydi
- Pub/Sub bor (kelajakda real-time uchun)

---

## 📦 MinIO (S3-mos)

### Sabab:
- **AWS S3 bilan API mos** — keyinchalik AWS'ga o'tish oson
- **O'zimizning serverda** — narx tejaymiz
- **Web UI** bor (admin uchun)
- **Bepul va ochiq kodli**

### Saqlanadigan fayllar:
- `books/` — original kitob fayllari (xususiy)
- `books-watermarked/{user_id}/` — watermarklangan, faqat sotib olgan uchun
- `covers/` — kitob muqovalari (ommaviy)
- `avatars/` — foydalanuvchi rasmlari (ommaviy)
- `demos/` — bepul demo fayllari (ommaviy)
- `blog/` — blog rasmlari

### Muqobil:
- Cloudflare R2 — S3 mos, arzon
- Backblaze B2 — eng arzon
- DigitalOcean Spaces — oddiy

---

## 🔍 Meilisearch (qidiruv)

### Sabab:
- **Tez** — millisekundlar ichida natija
- **Typo-tolerant** — xato yozsa ham topadi
- **Multilingual** — uz/ru/en yaxshi qo'llab-quvvatlanadi
- **Oddiy API** — RESTful
- **Yengil** — Elasticsearch'ga qaraganda kam resurs

### Muqobil:
- Elasticsearch — kuchli, lekin og'ir
- PostgreSQL FTS — yaxshi, lekin Meilisearch tezroq
- Typesense — Meilisearch'ga o'xshash

---

## 🐳 Docker + Docker Compose

### Sabab:
- **Bir xil environment** — dev/staging/prod
- **Tez ishga tushirish** — `docker compose up`
- **Izolyatsiya** — har bir servis o'z konteynerida
- **Scaling oson** — keyinchalik Kubernetes'ga ko'chirish oson

---

## 🌐 Nginx

### Sabab:
- **Reverse proxy** — bir necha servisni bitta porta yo'naltirish
- **SSL terminatsiya** — Let's Encrypt
- **Static fayl** — tez beradi
- **Load balancer** — kelajakda kerak bo'ladi
- **HTTP/2, HTTP/3** qo'llab-quvvatlash

---

## 💳 To'lov: Payme.uz

### Sabab:
- **O'zbekistondagi eng mashhur** to'lov tizimi
- **Merchant API** — dasturchi uchun yaxshi hujjatlar
- **Webhook** — to'lov tasdig'i avtomatik keladi
- **Karta** + **Hisob** orqali to'lov

### Kelajakda qo'shilishi mumkin:
- **Click.uz**
- **Uzcard / Humo** to'g'ridan-to'g'ri
- **Stripe** (chet ellik foydalanuvchilar uchun)

---

## 📧 Email yuborish

### Variantlar:

| Servis | Bepul | Plyuslar | Minuslar |
|--------|-------|----------|----------|
| **Gmail SMTP** | 500/kun | Oson | Limit kam |
| **Mailgun** | 5000/oy | Yaxshi API | Sozlash kerak |
| **Brevo (Sendinblue)** | 300/kun | Bepul, oson | Limit kam |
| **Amazon SES** | Arzon | Cheksiz | AWS sozlamasi |
| **Resend** | 3000/oy | Modern, oson | Yangi |

**Tavsiyam:** Resend yoki Brevo dan boshlash, keyin scaling kerak bo'lsa Mailgun yoki SES.

---

## 🔒 Xavfsizlik

### Vositalar:
- **bcrypt** — parol hashing
- **JWT** — autentifikatsiya
- **HTTPS** — Let's Encrypt (bepul SSL)
- **CORS** — to'g'ri sozlash
- **Rate limit** — slowapi (Python), Nginx limit_req
- **CSP** (Content Security Policy) headers
- **Cloudflare** (ixtiyoriy) — DDoS, bot himoyasi

---

## 📊 Monitoring (ixtiyoriy MVP da)

| Vosita | Vazifasi | Bepul plani |
|--------|----------|-------------|
| **Sentry** | Xato kuzatish | 5000 event/oy |
| **Uptime Robot** | Uptime monitoring | 50 monitor |
| **Better Stack** | Loglar va alertlar | 3 GB/oy |
| **Grafana Cloud** | Metrics | 10k metrics |

---

## 🎯 SEO

### Vositalar:
- **`@nuxtjs/seo`** — meta teglar avtomatik
- **`@nuxtjs/sitemap`** — sitemap.xml
- **`@nuxtjs/robots`** — robots.txt
- **JSON-LD** schema — Book, Person, Organization, BreadcrumbList
- **Google Search Console** — indexing
- **Yandex Webmaster** — yandex'da indexing (Rossiya foydalanuvchilari uchun)

---

## 🌍 CDN va DNS

### Cloudflare (bepul plan):
- ✅ DNS
- ✅ CDN (statik fayllar)
- ✅ DDoS himoya
- ✅ SSL (qo'shimcha qatlam)
- ✅ Analytics

---

## 🧪 Testing

### Backend:
- **pytest** — unit va integration testlar
- **httpx** — async test client
- **pytest-asyncio** — async testlar
- **factory_boy** — test ma'lumotlar yaratish

### Frontend:
- **Vitest** — unit testlar
- **Playwright** — E2E testlar (ixtiyoriy MVP da)

---

## 🔧 Development Tools

- **VS Code** + extension'lar:
  - Volar (Vue)
  - Python
  - Tailwind CSS IntelliSense
  - ESLint
  - Prettier
  - Docker
- **Git** + GitHub/GitLab
- **Postman** yoki **Insomnia** — API test
- **DBeaver** — Database GUI
- **MinIO Console** — fayllar GUI

---

## 📦 Package managers

- **Python**: `pip` + `pip-tools` yoki **`uv`** (yangi, tez)
- **Frontend**: **`pnpm`** (tez va disk-friendly) yoki `npm`

---

## 🤔 Nima uchun **bularni emas**?

| Texnologiya | Nima uchun emas |
|-------------|-----------------|
| **Django** | Ko'p ortiqcha narsa, FastAPI tezroq |
| **Express.js** | TypeScript bilan zaiflik, FastAPI tipga kuchli |
| **React** | Vue oson, kichik team uchun yaxshi |
| **Next.js** | Vue'da Nuxt bor, bir xil natija |
| **MySQL** | PostgreSQL kuchliroq (JSONB, transactions) |
| **MongoDB** | Bizning ma'lumotlar relational |
| **Bootstrap** | Tailwind moslashuvchanroq |
| **Material UI** | Tayyor stildan kelib chiqib emas, brending uchun custom |
| **Elasticsearch** | Meilisearch yengilroq va yetarli |

---

## 💵 Taxminiy oylik xarajatlar (production)

| Servis | Narxi |
|--------|-------|
| VPS server (4vCPU, 8GB RAM) | $20-40/oy |
| Domen | $10-15/yil |
| Cloudflare | bepul |
| Email (Brevo bepul plan) | bepul |
| Sentry (bepul plan) | bepul |
| Payme komissiya | har bir to'lovdan ~3% |
| **Jami minimal** | **~$25-45/oy** |

Foydalanuvchilar ko'paygach:
- DB alohida server: +$20
- Backup server: +$10
- Premium monitoring: +$25
- CDN keng band: +$20
- **Total ~$100-150/oy** (10k+ foydalanuvchi)

---

**Keyingi qadam:** [`03-backend/01-setup.md`](../03-backend/01-setup.md) — Backend o'rnatish.
