# Yo'l xaritasi — Rivojlanish bosqichlari

Anjumanlar.com'ni 0'dan ishchi saytga olib chiqish bo'yicha 8-10 haftalik MVP rejasi.

## Umumiy qarash

```
Hafta 1-2   ▸ Loyihaga tayyorgarlik, asos qurish
Hafta 3-4   ▸ Backend asosiy funksionallik
Hafta 5-6   ▸ Frontend asosiy sahifalar
Hafta 7     ▸ To'lov tizimi va integratsiya
Hafta 8     ▸ Admin panel va muallif kabineti
Hafta 9     ▸ Sayqallash, test, dizayn
Hafta 10    ▸ Deploy va launch
```

**Jami:** 10 hafta MVP uchun (bitta developer, kuniga 4-6 soat).
**Komanda bilan (2-3 kishi):** 5-6 hafta.

---

## Sprint 1: Tayyorgarlik va arxitektura (Hafta 1-2)

### Maqsad
Loyihaning skeletini yaratish: server, DB, asosiy infratuzilma.

### Bajariladigan ishlar

**Loyihaga tayyorgarlik:**
- [ ] Domain sotib olish: anjumanlar.com
- [ ] VPS sozlash (DigitalOcean / Hetzner — $20/oy)
- [ ] GitHub repository yaratish (private)
- [ ] Project management (Trello yoki Notion)
- [ ] Figma'da brendlik kontseptsiya (logo, ranglar)

**Infratuzilma:**
- [ ] Docker va Docker Compose o'rnatish
- [ ] Loyiha folder strukturasi (monorepo)
- [ ] PostgreSQL container
- [ ] Redis container
- [ ] MinIO container
- [ ] Meilisearch container
- [ ] Nginx config (development)

**Backend skelet:**
- [ ] FastAPI loyihasi
- [ ] SQLAlchemy + Alembic
- [ ] `pyproject.toml` to'liq
- [ ] `.env.example`
- [ ] Health check endpoint (`/health`)
- [ ] CI/CD pipeline (GitHub Actions — test va lint)

**Frontend skelet:**
- [ ] Nuxt 3 loyihasi
- [ ] Tailwind CSS sozlash
- [ ] i18n modul (uz/ru/en)
- [ ] Color mode (dark/light)
- [ ] Pinia store
- [ ] Asosiy layoutlar

**Database:**
- [ ] DB schema ER diagramma
- [ ] Migration: users, author_profiles, categories, books

### Sprint 1 natijasi

```
✓ http://localhost:3000 — Nuxt landing
✓ http://localhost:8000/docs — FastAPI swagger
✓ DB: 4 jadval mavjud
✓ Asosiy auth (register, login JWT)
```

---

## Sprint 2: Backend asosiy logika (Hafta 3-4)

### Maqsad
Saytning asosiy ish jarayonlari: kitob qo'shish, ko'rish, qidirish.

### Bajariladigan ishlar

**Authentication:**
- [ ] Register endpoint (email + parol)
- [ ] Login (JWT access + refresh tokenlar)
- [ ] Email tasdiqlash (SMTP, MailHog dev'da)
- [ ] Parolni tiklash flow
- [ ] Role-based access (`require_roles` decorator)
- [ ] Rate limiting (slowapi)

**Kitob CRUD:**
- [ ] Kitob yaratish (muallif)
- [ ] Kitob ro'yxati (filter, pagination)
- [ ] Kitob batafsil (slug bilan)
- [ ] Kitob tahrirlash
- [ ] Kitob status (draft → moderation → published)
- [ ] Kategoriyalar (CRUD)
- [ ] Tag tizimi

**File upload:**
- [ ] PDF yuklash → MinIO
- [ ] Cover image yuklash + resize
- [ ] Demo PDF generatsiya (birinchi 10 sahifa)
- [ ] PDF watermark logikasi (Celery task)

**Qidiruv:**
- [ ] Meilisearch index sozlash
- [ ] Kitoblarni Meilisearch'ga sinxronlash
- [ ] Search endpoint
- [ ] Facet filter (kategoriya, narx, til)

**Profile:**
- [ ] User profile endpoint
- [ ] Avatar yuklash
- [ ] Author profile (bio, bank info)

### Sprint 2 natijasi

```
✓ Muallif kitob yuklay oladi
✓ Kitoblar ro'yxati ko'rinadi
✓ Qidiruv ishlaydi
✓ Avtorizatsiya to'liq
```

---

## Sprint 3: Frontend asosiy sahifalar (Hafta 5-6)

### Maqsad
Foydalanuvchi sayt bilan to'liq vizual ishlay olsin.

### Bajariladigan ishlar

**Asosiy sahifalar:**
- [ ] Bosh sahifa (Hero, top kitoblar, kategoriyalar)
- [ ] Katalog sahifasi (grid, filter, pagination)
- [ ] Kitob batafsil sahifasi (cover, info, tabs)
- [ ] PDF demo viewer (PDF.js)
- [ ] Muallif profil sahifasi
- [ ] Kategoriya sahifasi
- [ ] Qidiruv natijalari sahifasi

**Auth sahifalar:**
- [ ] Login
- [ ] Register
- [ ] Parolni unutdim
- [ ] Email tasdiqlash

**Foydalanuvchi sahifalari:**
- [ ] Profil sozlamalari
- [ ] Mening kitoblarim (sotib olingan)
- [ ] Sevimlilar (wishlist)
- [ ] Tarix (orders)

**Komponentlar:**
- [ ] BookCard (grid va list variantlar)
- [ ] Header (sticky, theme toggle, language switcher)
- [ ] Footer
- [ ] Search bar (autocomplete)
- [ ] Filter sidebar
- [ ] Pagination
- [ ] Breadcrumbs
- [ ] Modal komponenti
- [ ] Toast bildirishnomalar

**i18n:**
- [ ] uz/ru/en tarjimalar
- [ ] Til o'tkazgich
- [ ] hreflang teglar

**Dark mode:**
- [ ] Toggle 3-holat (light/dark/system)
- [ ] CSS variables to'liq

### Sprint 3 natijasi

```
✓ Foydalanuvchi saytda mavjud sahifalarni ko'ra oladi
✓ Qidiruv ishlaydi
✓ Profil va auth ishlaydi
✓ Dark mode va 3 til ishlaydi
```

---

## Sprint 4: To'lov tizimi (Hafta 7)

### Maqsad
Kitobni sotib olib, yuklab olish to'liq ishlasin.

### Bajariladigan ishlar

**Order va Cart:**
- [ ] Order yaratish endpoint
- [ ] Order holatlar (pending, paid, expired, cancelled)
- [ ] Pending order'larni 30 daqiqada expire qilish (Celery beat)

**Payme integratsiya:**
- [ ] Payme checkout URL generatsiya
- [ ] Webhook endpoint (CheckPerformTransaction, CreateTransaction, va h.k.)
- [ ] Webhook Basic Auth
- [ ] Transaction sinxronizatsiya
- [ ] Test mode + sandbox URL

**Sotib olishdan keyingi flow:**
- [ ] Library'ga qo'shish (user_libraries)
- [ ] Watermark PDF tayyorlash (Celery)
- [ ] Email yuborish ("Kitob mavjud")
- [ ] Author balance'ga 85% qo'shish

**Frontend checkout:**
- [ ] Cart sahifasi
- [ ] Checkout flow
- [ ] To'lov sahifasi (Payme redirect)
- [ ] Success sahifasi
- [ ] Failed sahifasi

**Withdrawal:**
- [ ] Author balansni ko'rish
- [ ] Withdrawal so'rovi yaratish
- [ ] Admin withdrawal'ni tasdiqlash

### Sprint 4 natijasi

```
✓ Foydalanuvchi kitob sotib oladi
✓ Payme to'lovi muvaffaqiyatli o'tadi
✓ PDF watermark bilan yuklanadi
✓ Muallif balansi to'g'ri ko'rsatiladi
```

---

## Sprint 5: Admin va Muallif kabineti (Hafta 8)

### Maqsad
Boshqaruv va kontrol panellari.

### Bajariladigan ishlar

**Admin panel:**
- [ ] Dashboard (statistika kartochkalari)
- [ ] Foydalanuvchilar ro'yxati
- [ ] Mualliflar boshqaruvi
- [ ] Kitob moderatsiyasi (draft → review → published / rejected)
- [ ] Kategoriya CRUD
- [ ] Buyurtmalar
- [ ] To'lovlar
- [ ] Withdrawal so'rovlar
- [ ] Blog post CRUD
- [ ] Settings (komissiya foiz va h.k.)

**Muallif kabineti:**
- [ ] Dashboard (sotuvlar grafigi, oxirgi buyurtmalar)
- [ ] Mening kitoblarim (CRUD)
- [ ] Yangi kitob qo'shish (multi-step form)
- [ ] Sotuvlar analitikasi
- [ ] Balans va withdrawal so'rovlar
- [ ] Statistika eksport (CSV)

**Sharhlar:**
- [ ] Reviews CRUD (faqat sotib olganlar)
- [ ] Reyting hisoblash
- [ ] Admin review moderatsiyasi

**Bildirishnomalar:**
- [ ] In-app bildirishnomalar
- [ ] Email bildirishnomalar (yangi sotuv, withdrawal status)

### Sprint 5 natijasi

```
✓ Admin to'liq saytni boshqara oladi
✓ Muallif o'z kabinetidan ishlay oladi
✓ Bildirishnomalar yetib boradi
```

---

## Sprint 6: Sayqallash va test (Hafta 9)

### Maqsad
Sayt sifatini production darajaga olib chiqish.

### Bajariladigan ishlar

**Dizayn sayqallash:**
- [ ] Barcha sahifalar Figma dizaynga mos kelishi
- [ ] Mobile responsive tekshirish (iPhone SE, iPhone 14, Galaxy S22)
- [ ] Tablet ko'rinish
- [ ] Loading skeletonlar
- [ ] Empty states
- [ ] Animatsiyalar (yumshoq transitions)

**SEO:**
- [ ] Meta teglar har sahifada
- [ ] JSON-LD (Book, Person, Organization, BreadcrumbList)
- [ ] sitemap.xml dinamik
- [ ] robots.txt
- [ ] hreflang har sahifada
- [ ] OG rasm dinamik generatsiya
- [ ] Google Search Console + Yandex Webmaster

**Tezlik:**
- [ ] Image optimizatsiya (WebP, lazy load)
- [ ] CSS/JS minify
- [ ] PageSpeed 80+ mobile
- [ ] Database query'lar optimallashtirilgan
- [ ] N+1 query'lar yo'q
- [ ] Redis cache (kategoriyalar, kitob ro'yxati)

**Testlar:**
- [ ] Backend: pytest — auth, books, orders, payments
- [ ] Frontend: Vitest — komponentlar
- [ ] E2E: Playwright — asosiy flow'lar (register, buy, download)
- [ ] Load test (k6 yoki Locust) — 100 RPS bardosh

**Bug fix:**
- [ ] Beta testerlardan feedback yig'ish
- [ ] Bug bugun ham fix qilish
- [ ] UX improvement'lar

**Statik sahifalar:**
- [ ] Biz haqimizda
- [ ] Foydalanish shartlari
- [ ] Maxfiylik siyosati
- [ ] Oferta
- [ ] FAQ
- [ ] Bog'lanish

### Sprint 6 natijasi

```
✓ Sayt mukammal, bugsiz
✓ Tezlik ajoyib
✓ SEO to'liq sozlangan
✓ Mobile UX qiyinchilik tug'dirmaydi
```

---

## Sprint 7: Production deploy va launch (Hafta 10)

### Maqsad
Saytni jonli serverda ishga tushirish.

### Bajariladigan ishlar

**Server:**
- [ ] Production VPS sozlash
- [ ] Domain DNS sozlash
- [ ] SSH key, firewall, fail2ban
- [ ] Docker production tugallandi
- [ ] Nginx + SSL (Let's Encrypt)
- [ ] Backup cron job
- [ ] Monitoring (Uptime Robot)
- [ ] Sentry sozlash

**Production checklistdan o'tish:**
- [ ] [Production Checklist](../07-deployment/03-production-checklist.md)dagi barcha bandlar bajarilgan

**Payme:**
- [ ] Production credentials olish
- [ ] Webhook URL ro'yxatdan o'tkazish
- [ ] Real to'lov test (kichik summa)

**Soft launch:**
- [ ] 10-20 beta foydalanuvchi
- [ ] 3-5 muallif demo kontent yuklaydi
- [ ] 1 hafta monitoring

**Public launch:**
- [ ] Social media e'lon (Telegram, Facebook, Instagram)
- [ ] Press release (mahalliy IT bloglar, sayt'lar)
- [ ] Universitet va ilmiy institutlar bilan tanishtirish
- [ ] Google Ads / Yandex Direct birinchi kampaniyasi
- [ ] Influencer outreach (akademik telegram kanallari)

### Sprint 7 natijasi

```
🚀 Anjumanlar.com jonli!
✓ https://anjumanlar.com — ishlaydi
✓ Birinchi mualliflar va o'quvchilar ro'yxatdan o'tdi
✓ Birinchi to'lov muvaffaqiyatli amalga oshdi
```

---

## Launch'dan keyin: 1-3 oy

### Birinchi oy
- Bug fix va UX yaxshilash (foydalanuvchi feedback'iga ko'ra)
- Kontent marketing (haftada 1-2 blog post)
- Mualliflar bilan ishlash (onboarding)
- Email kampaniyalar
- SEO monitoring va improvement

### 2-oy
- Yangi funksiyalar (foydalanuvchi so'roviga ko'ra)
- Affiliate dastur (referallar)
- Telegram bot integratsiya (yangi kitob xabarlari)
- Mobile app rejasini boshlash (agar talab bo'lsa)

### 3-oy
- Mobile aplikatsiya (React Native yoki Flutter)
- Audiokitob qo'llab-quvvatlash
- Subscription model (oylik to'lov bilan limitsiz kitob)

## Phase 2 (3-6 oy)

- [ ] Audio kitoblar
- [ ] Mobil ilova (iOS, Android)
- [ ] Affiliate / referral dastur
- [ ] Subscription model
- [ ] Author analytics (chuqurroq)
- [ ] Multi-vendor wallet integratsiya (Click, Uzcard)
- [ ] DOI integratsiya (akademik)

## Phase 3 (6-12 oy)

- [ ] AI tavsiya tizimi (kitob rekomendatsiyalari)
- [ ] Foydalanuvchi-mualliflar uchun yozish vositalari (online editor)
- [ ] Kitob nashri xizmatlari (POD — print on demand)
- [ ] Konferensiyalar va event'lar
- [ ] Akademik jurnal nashri funksionalligi

## Vaqt taqsimoti (taxminiy, bitta developer)

| Sprint | Backend | Frontend | DevOps | Dizayn | Test |
|--------|---------|----------|--------|--------|------|
| 1 | 30% | 20% | 30% | 15% | 5% |
| 2 | 60% | 20% | 5% | 5% | 10% |
| 3 | 20% | 60% | 5% | 10% | 5% |
| 4 | 40% | 35% | 10% | 5% | 10% |
| 5 | 40% | 45% | 5% | 5% | 5% |
| 6 | 20% | 25% | 10% | 25% | 20% |
| 7 | 10% | 10% | 60% | 5% | 15% |

---

**Keyingi qadam:** [MVP Checklist](./02-mvp-checklist.md)
