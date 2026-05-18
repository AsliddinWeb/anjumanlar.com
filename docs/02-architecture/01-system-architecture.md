# 01. Tizim Arxitekturasi (System Architecture)

> Anjumanlar.com — mikroservislarga juda yaqin **monolitik + servisli** arxitekturada quriladi. Bu kichik komandalar uchun optimaldir.

---

## 🏗 Yuqori darajadagi arxitektura

```
┌──────────────────────────────────────────────────────────────────┐
│                     INTERNET (Foydalanuvchilar)                  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Nginx (Reverse Proxy) │
                    │  + Let's Encrypt SSL   │
                    │  + Rate Limiting       │
                    └─────┬─────────────┬───┘
                          │             │
                          │             │ /api/*
                          ▼             ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  Frontend (Nuxt) │  │ Backend (FastAPI)│
              │  Vue 3 + SSR     │  │  Python 3.12     │
              │  Port: 3000      │  │  Port: 8000      │
              └──────────────────┘  └─────────┬────────┘
                                              │
                ┌─────────────────────────────┼─────────────────────────┐
                │                             │                         │
                ▼                             ▼                         ▼
        ┌───────────────┐           ┌─────────────────┐         ┌──────────────┐
        │  PostgreSQL   │           │      Redis      │         │    MinIO     │
        │  (asosiy DB)  │           │  (kesh, navbat) │         │  (S3 fayllar)│
        │  Port: 5432   │           │  Port: 6379     │         │  Port: 9000  │
        └───────────────┘           └─────────────────┘         └──────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Celery Workers  │
                                    │ (email, PDF      │
                                    │  watermark, etc) │
                                    └──────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │   Meilisearch    │
                                    │ (kitob qidiruv)  │
                                    │  Port: 7700      │
                                    └──────────────────┘

         ┌──────────────────────────────────────────────────┐
         │   Tashqi servislar:                              │
         │   • Payme.uz Merchant API (to'lovlar)            │
         │   • SMTP (Gmail / Mailgun / SES — emaillar)      │
         │   • Sentry (xato monitoringi)                    │
         │   • Cloudflare (CDN, DDoS himoya — ixtiyoriy)    │
         └──────────────────────────────────────────────────┘
```

---

## 📦 Servislar va ularning vazifasi

### 1. **Nginx** (Reverse Proxy)
- Barcha so'rovlarni qabul qilib, kerakli servisga yo'naltiradi
- SSL terminatsiyasi (HTTPS)
- Static fayllarni keshlash
- Rate limiting (DDoS himoyasi)
- Gzip/Brotli siqish

**Konfiguratsiya:** `/nginx/nginx.conf` da

### 2. **Frontend** (Vue.js / Nuxt.js)
- **Nuxt 3** ishlatamiz — Vue.js'ning SSR/SSG framework'i
- Sabab: SEO uchun majburiy
- Tailwind CSS bilan stillanadi
- Pinia — state management
- vue-i18n — ko'p tillilik
- Axios yoki Fetch API — backend bilan aloqa

### 3. **Backend** (FastAPI)
- REST API
- Python 3.12+
- SQLAlchemy 2.0 (ORM)
- Alembic (migration)
- Pydantic v2 (validatsiya)
- JWT autentifikatsiya
- OpenAPI/Swagger avtomatik

### 4. **PostgreSQL** (asosiy ma'lumotlar bazasi)
- Foydalanuvchilar, kitoblar, buyurtmalar, sharhlar
- 16-versiya
- JSONB ishlatish ko'p tilli matnlar uchun

### 5. **Redis** (kesh va navbat)
- Sessiya saqlash
- Tez-tez ishlatiladigan ma'lumotlarni keshlash (kategoriyalar, top kitoblar)
- Celery uchun message broker
- Rate limit counter

### 6. **MinIO** (fayllar saqlash)
- S3-mos keluvchi obyekt do'koni
- Kitoblar (PDF, EPUB)
- Muqovalar (JPG, PNG)
- Foydalanuvchi avatarlari
- Sotib olingan watermarklangan PDF'lar

### 7. **Celery + Redis** (background tasks)
Asinxron vazifalar:
- Email yuborish (welcome, parol tiklash, buyurtma)
- PDF watermark qo'shish (sotib olganda)
- PDF dan thumbnail yaratish
- Sotuv statistikasi hisoblash
- Database backup
- Search indexini yangilash

### 8. **Meilisearch** (qidiruv)
- Tezkor, typo-tolerant qidiruv
- Kitob nomlari va annotatsiyalari indexlanadi
- 3 tilda qidiruv qo'llab-quvvatlanadi

---

## 🔄 Asosiy oqimlar (Flows)

### A. Kitob sotib olish oqimi

```
1. O'quvchi → Frontend → "Sotib ol" tugmasi
2. Frontend → POST /api/orders {book_id}
3. Backend → DB: buyurtma yaratish (status: pending)
4. Backend → Payme API: invoice yaratish
5. Backend → Frontend: payment_url qaytaradi
6. Frontend → Payme sahifasiga redirect
7. Payme → foydalanuvchi to'laydi
8. Payme → Backend webhook (POST /api/payments/payme/callback)
9. Backend → DB: buyurtma "paid" qiladi
10. Backend → Celery: PDF watermark task
11. Celery → MinIO'dan PDF olib, watermark qo'shadi
12. Celery → MinIO'ga saqlaydi (yangi fayl)
13. Celery → Email yuboradi: "Kitobingiz tayyor"
14. Frontend → /payment/success sahifa ko'rsatiladi
```

### B. Kitob yuklash oqimi

```
1. Muallif → Frontend → "Yangi kitob" formasi
2. Frontend → POST /api/books (forma + PDF + muqova)
3. Backend → fayllarni MinIO'ga yuklaydi
4. Backend → DB: kitob yaratiladi (status: draft)
5. Muallif → "Nashr qilish" tugmasi
6. Backend → status: pending
7. Backend → Celery: PDF metadata olish (sahifa soni)
8. Admin → ko'radi va tasdiqlaydi → status: approved
9. Backend → Meilisearch: index'ga qo'shadi
10. Backend → Email muallifga: "Kitob tasdiqlandi"
11. Kitob barcha foydalanuvchilarga ko'rinadi
```

### C. Qidiruv oqimi

```
1. Foydalanuvchi → qidiruv satriga yozadi
2. Frontend → debounce (300ms)
3. Frontend → GET /api/search?q=...&lang=uz
4. Backend → Meilisearch'ga so'rov
5. Meilisearch → natijalar qaytaradi
6. Backend → keshlanadi (Redis, 5 daq)
7. Frontend → ko'rsatadi
```

---

## 🔒 Xavfsizlik qatlamlari

```
1. Cloudflare (ixtiyoriy) — DDoS, bot himoyasi
2. Nginx — rate limiting, request size cheklash
3. FastAPI middleware — CORS, JWT verification
4. Pydantic — input validation
5. SQLAlchemy ORM — SQL injection himoyasi
6. bcrypt — parol hashing
7. HTTPS — barcha trafik shifrlangan
8. Signed URLs — MinIO fayllari uchun
9. PDF watermark — kontent himoyasi
```

---

## 📊 Ma'lumotlar oqimi (Data Flow)

### Read-heavy operatsiyalar (ko'p o'qiladi):
- Kitoblar ro'yxati → Redis kesh (5-10 daq)
- Kategoriyalar → Redis kesh (1 soat)
- Top mualliflar → Redis kesh (1 soat)
- Kitob tafsilot → har bir kitob alohida kesh (1 soat)

### Write-heavy operatsiyalar (ko'p yoziladi):
- Buyurtmalar → bevosita DB
- Sharhlar → bevosita DB
- Sotuv hisoblari → har 5 daqiqada batched update

---

## 🌐 Mintaqaviy joylashuv (Hosting)

Tavsiyalar:
- **Production server:** O'zbekistondagi VPS (UzCloud, Beeline Cloud) yoki Russia (Selectel, Timeweb) — past latency
- **Backup server:** Boshqa mintaqa (xavfsizlik uchun)
- **CDN:** Cloudflare (bepul) — static fayllar uchun
- **DNS:** Cloudflare yoki tashqi servis

Minimal server konfiguratsiyasi (boshlanish uchun):
- 4 vCPU
- 8 GB RAM
- 100 GB SSD
- 1 TB traffic

---

## 🔧 Servislar o'rtasidagi aloqa

### Sinxron (HTTP):
- Frontend ↔ Backend (REST API)
- Backend ↔ Payme API
- Backend ↔ Meilisearch

### Asinxron (Message Queue):
- Backend → Celery (Redis broker)
- Celery → Email (SMTP)
- Celery → MinIO

### To'g'ridan-to'g'ri TCP:
- Backend ↔ PostgreSQL
- Backend ↔ Redis (kesh)
- Celery ↔ MinIO

---

## 🚨 Monitoring va loglar

### Loglar:
- Backend → STDOUT (Docker logs)
- Nginx → access.log, error.log
- Celery → STDOUT
- PostgreSQL → slow query log

### Monitoring (Production):
- **Sentry** — backend va frontend xatolari
- **Prometheus + Grafana** (ixtiyoriy) — metrics
- **Uptime Robot** (bepul) — uptime nazorat
- **Cloudflare Analytics** — trafik tahlil

---

## 📈 Scaling strategiyasi

### Bosqich 1 (0-1000 foydalanuvchi/kun):
- Bitta server hammasi
- Docker Compose

### Bosqich 2 (1000-10000 foydalanuvchi/kun):
- Backend alohida server
- Database alohida server
- Redis va MinIO ham

### Bosqich 3 (10000+ foydalanuvchi/kun):
- Backend horizontal scaling (3-5 instance)
- Load balancer
- PostgreSQL read replicas
- CDN majburiy
- Kubernetes ga ko'chish

---

## ⚙️ Texnologiyalar versiyalari

| Texnologiya | Versiya | Sabab |
|-------------|---------|-------|
| Python | 3.12+ | Eng yangi, tez |
| FastAPI | 0.110+ | Async, OpenAPI |
| Vue.js | 3.4+ | Composition API |
| Nuxt | 3.10+ | SSR, SEO |
| PostgreSQL | 16 | LTS, JSONB |
| Redis | 7 | Latest stable |
| Node.js | 20 LTS | Frontend build |
| Docker | 24+ | Compose v2 |
| Nginx | 1.25+ | HTTP/3 |
| Meilisearch | 1.6+ | Latest |
| MinIO | latest | S3 compatible |

---

**Keyingi qadam:** [`02-folder-structure.md`](./02-folder-structure.md) — Loyiha papkalar tuzilmasi.
