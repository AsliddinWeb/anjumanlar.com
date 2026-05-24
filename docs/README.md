# 📚 Monografiya — Monografiya Sotuvi Platformasi

> Mualliflar uchun monografiyalarni yuklash va sotish platformasi. Onlayn kitob do'koni dizaynida, ko'p tilli, professional va to'liq Docker bilan deploy qilinadigan loyiha.

---

## 🎯 Loyiha Haqida Qisqacha

**Monografiya** — bu mualliflar o'z monografiyalarini (kitoblar) yuklab, sotish yoki bepul tarqatish imkonini beradigan platforma. Sayt **payme.uz** orqali to'lov qabul qiladi, **3 ta tilda** (O'zbek, Rus, Ingliz) ishlaydi va **kunduzgi/tungi rejim**ga ega.

### Asosiy texnologiyalar

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | **FastAPI** (Python 3.12+) |
| Frontend | **Vue.js 3** (Composition API + TypeScript) |
| Dizayn | **Tailwind CSS** + Headless UI |
| Ma'lumotlar bazasi | **PostgreSQL 16** |
| Kesh va navbat | **Redis 7** |
| Faylar | **MinIO** (S3-mos keluvchi) |
| Qidiruv | **Meilisearch** |
| SEO | **Vue Meta** + **server-side rendering** (Nuxt SSR rejim) |
| Konteynerlash | **Docker + Docker Compose** |
| Reverse proxy | **Nginx** + **Let's Encrypt** |
| Monitoring | **Prometheus + Grafana** (ixtiyoriy) |
| To'lov | **Payme.uz** Merchant API |

---

## 📂 Hujjatlar tuzilmasi

Quyidagi tartibda o'qish tavsiya etiladi:

### 1. Umumiy ko'rinish
- [`01-overview/01-project-summary.md`](./01-overview/01-project-summary.md) — Loyihaning maqsadi, foydalanuvchi tiplari
- [`01-overview/02-user-roles.md`](./01-overview/02-user-roles.md) — Rollar va ularning huquqlari
- [`01-overview/03-pages-list.md`](./01-overview/03-pages-list.md) — Saytdagi barcha sahifalar ro'yxati
- [`01-overview/04-features.md`](./01-overview/04-features.md) — Funksiyalar to'liq ro'yxati

### 2. Arxitektura
- [`02-architecture/01-system-architecture.md`](./02-architecture/01-system-architecture.md) — Tizim arxitekturasi
- [`02-architecture/02-folder-structure.md`](./02-architecture/02-folder-structure.md) — Loyiha papkalar tuzilmasi
- [`02-architecture/03-tech-stack.md`](./02-architecture/03-tech-stack.md) — Texnologiyalar va sabablari

### 3. Backend (FastAPI)
- [`03-backend/01-setup.md`](./03-backend/01-setup.md) — O'rnatish va ishga tushirish
- [`03-backend/02-api-endpoints.md`](./03-backend/02-api-endpoints.md) — Barcha API endpointlar
- [`03-backend/03-authentication.md`](./03-backend/03-authentication.md) — JWT autentifikatsiya
- [`03-backend/04-file-upload.md`](./03-backend/04-file-upload.md) — Kitoblarni yuklash logikasi

### 4. Frontend (Vue.js)
- [`04-frontend/01-setup.md`](./04-frontend/01-setup.md) — Vue loyihasini sozlash
- [`04-frontend/02-pages-and-routes.md`](./04-frontend/02-pages-and-routes.md) — Sahifalar va marshrutlar
- [`04-frontend/03-components.md`](./04-frontend/03-components.md) — Komponentlar ro'yxati
- [`04-frontend/04-i18n.md`](./04-frontend/04-i18n.md) — Ko'p tillilik (uz/ru/en)
- [`04-frontend/05-theme-system.md`](./04-frontend/05-theme-system.md) — Kunduzgi/tungi rejim

### 5. Ma'lumotlar bazasi
- [`05-database/01-schema.md`](./05-database/01-schema.md) — Jadvallar tuzilmasi
- [`05-database/02-migrations.md`](./05-database/02-migrations.md) — Migrationlar (Alembic)
- [`05-database/03-seed-data.md`](./05-database/03-seed-data.md) — Boshlang'ich ma'lumotlar

### 6. To'lov tizimi
- [`06-payment/01-payme-integration.md`](./06-payment/01-payme-integration.md) — Payme.uz integratsiyasi
- [`06-payment/02-payment-flow.md`](./06-payment/02-payment-flow.md) — To'lov jarayoni

### 7. Deployment
- [`07-deployment/01-docker-setup.md`](./07-deployment/01-docker-setup.md) — Docker konfiguratsiya
- [`07-deployment/02-nginx-ssl.md`](./07-deployment/02-nginx-ssl.md) — Nginx va SSL
- [`07-deployment/03-production-checklist.md`](./07-deployment/03-production-checklist.md) — Production tekshiruv ro'yxati

### 8. Dizayn tizimi
- [`08-design/01-design-system.md`](./08-design/01-design-system.md) — Ranglar, shriftlar, tipografika
- [`08-design/02-ui-guidelines.md`](./08-design/02-ui-guidelines.md) — UI tamoyillari va kitob do'koni stili

### 9. SEO
- [`09-seo/01-seo-strategy.md`](./09-seo/01-seo-strategy.md) — SEO strategiyasi
- [`09-seo/02-meta-sitemap.md`](./09-seo/02-meta-sitemap.md) — Meta teglar, sitemap, robots.txt

### 10. Yo'l xaritasi
- [`10-roadmap/01-development-phases.md`](./10-roadmap/01-development-phases.md) — Bosqichma-bosqich rivojlanish
- [`10-roadmap/02-mvp-checklist.md`](./10-roadmap/02-mvp-checklist.md) — MVP uchun tekshiruv ro'yxati

---

## ⚡ Tez boshlash (Quick Start)

```bash
# 1. Repozitoriyani klonlash
git clone <your-repo-url> monografiya
cd monografiya

# 2. Environment fayllarni sozlash
cp .env.example .env
# .env faylni o'z qiymatlaringiz bilan to'ldiring

# 3. Docker bilan ishga tushirish
docker compose up -d

# 4. Migration va seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed

# 5. Brauzerda ochish
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Admin: http://localhost:3000/admin
```

---

## 🗂 Tavsiya etilgan o'qish tartibi

Agar siz **birinchi marta** loyihaga kirib kelayotgan bo'lsangiz:

1. ✅ Ushbu `README.md` ni to'liq o'qing
2. ✅ `01-overview/` papkasidagi 4 ta faylni ketma-ket o'qing
3. ✅ `02-architecture/` papkasidan tizim arxitekturasini tushuning
4. ✅ `10-roadmap/01-development-phases.md` orqali ishni qaysi bosqichdan boshlashni rejalashtiring
5. ✅ Keyin Backend yoki Frontend papkasidan boshlab implement qiling

---

## 📞 Yordam

Har bir `.md` faylda alohida bo'lim mavjud:
- **Maqsad** — nima uchun kerak
- **Implementatsiya** — qanday qilinadi
- **Misollar** — kod misollar
- **Eslatmalar** — muhim nuanslar

---

**Muallif uchun eslatma:** Bu hujjatlar Claude (Anthropic) yordamida tayyorlangan. Har bir hujjat ishlab chiqishni boshlash uchun yetarli darajada batafsil yozilgan, lekin loyihangiz davomida yangilab borish tavsiya etiladi.
