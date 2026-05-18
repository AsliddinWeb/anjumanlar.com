# MVP Checklist — Anjumanlar.com

MVP (Minimum Viable Product) — bu launch'ga kerakli minimum funksionallik. Bu checklist orqali ishlaringizni kuzatib boring.

## Belgilash

```
[ ] — bajarilmagan
[x] — bajarilgan
[~] — qisman bajarilgan
```

---

## 1. Loyiha tayyorgarligi

- [ ] Domain sotib olingan: `anjumanlar.com`
- [ ] DNS sozlangan
- [ ] VPS server (4GB RAM, 2 CPU, 50GB SSD)
- [ ] GitHub repository (private)
- [ ] `.gitignore` to'g'ri
- [ ] README.md asosiy ko'rsatmalar bilan
- [ ] `.env.example` to'liq

## 2. Infrastructure (Docker)

- [ ] `docker-compose.yml` ishlaydi
- [ ] PostgreSQL 16 container
- [ ] Redis 7 container
- [ ] MinIO container
- [ ] Meilisearch container
- [ ] Backend container
- [ ] Frontend container
- [ ] Celery worker container
- [ ] Celery beat container
- [ ] Nginx (production)
- [ ] MailHog (dev only)

## 3. Database

- [ ] Schema yaratilgan (`05-database/01-schema.md`)
- [ ] Alembic migration'lar mavjud
- [ ] Seed data scripti (`scripts/seed.py`)
- [ ] Backup scripti (`scripts/backup.sh`)
- [ ] Indexlar qo'shilgan (search, foreign keys)
- [ ] Triggerlar (updated_at, rating update)

### Asosiy jadvallar:
- [ ] `users`
- [ ] `author_profiles`
- [ ] `categories`
- [ ] `books`
- [ ] `book_categories`
- [ ] `orders`
- [ ] `order_items`
- [ ] `payments`
- [ ] `user_libraries`
- [ ] `wishlists`
- [ ] `reviews`
- [ ] `withdrawals`
- [ ] `blog_posts`
- [ ] `settings`
- [ ] `notifications`
- [ ] `audit_logs`
- [ ] `refresh_tokens`

## 4. Backend (FastAPI)

### Auth
- [ ] POST `/api/v1/auth/register`
- [ ] POST `/api/v1/auth/login`
- [ ] POST `/api/v1/auth/refresh`
- [ ] POST `/api/v1/auth/logout`
- [ ] POST `/api/v1/auth/forgot-password`
- [ ] POST `/api/v1/auth/reset-password`
- [ ] POST `/api/v1/auth/verify-email`
- [ ] GET `/api/v1/auth/me`

### Users
- [ ] GET `/api/v1/users/me`
- [ ] PATCH `/api/v1/users/me`
- [ ] POST `/api/v1/users/me/avatar`
- [ ] DELETE `/api/v1/users/me`

### Books
- [ ] GET `/api/v1/books` (filter, search, sort)
- [ ] GET `/api/v1/books/{slug}`
- [ ] POST `/api/v1/books` (author)
- [ ] PATCH `/api/v1/books/{id}` (author)
- [ ] DELETE `/api/v1/books/{id}` (author)
- [ ] POST `/api/v1/books/{id}/cover`
- [ ] POST `/api/v1/books/{id}/file`
- [ ] GET `/api/v1/books/{id}/demo`
- [ ] GET `/api/v1/books/{id}/download` (faqat sotib olganlar)

### Categories
- [ ] GET `/api/v1/categories`
- [ ] GET `/api/v1/categories/{slug}`
- [ ] POST `/api/v1/categories` (admin)
- [ ] PATCH `/api/v1/categories/{id}` (admin)
- [ ] DELETE `/api/v1/categories/{id}` (admin)

### Orders
- [ ] POST `/api/v1/orders` (create)
- [ ] GET `/api/v1/orders/me`
- [ ] GET `/api/v1/orders/{id}`
- [ ] POST `/api/v1/orders/{id}/cancel`

### Payments
- [ ] POST `/api/v1/payments/payme/initiate`
- [ ] POST `/api/v1/payments/payme/webhook` (Basic Auth)

### Reviews
- [ ] GET `/api/v1/books/{id}/reviews`
- [ ] POST `/api/v1/books/{id}/reviews`
- [ ] PATCH `/api/v1/reviews/{id}`
- [ ] DELETE `/api/v1/reviews/{id}`

### Search
- [ ] GET `/api/v1/search?q=...`

### Authors
- [ ] GET `/api/v1/authors`
- [ ] GET `/api/v1/authors/{slug}`
- [ ] GET `/api/v1/authors/{id}/books`

### Withdrawals (author)
- [ ] GET `/api/v1/withdrawals/me`
- [ ] POST `/api/v1/withdrawals` (so'rov)
- [ ] GET `/api/v1/withdrawals/me/balance`

### Admin
- [ ] GET `/api/v1/admin/dashboard`
- [ ] GET `/api/v1/admin/users`
- [ ] PATCH `/api/v1/admin/users/{id}`
- [ ] DELETE `/api/v1/admin/users/{id}`
- [ ] GET `/api/v1/admin/books/moderation`
- [ ] POST `/api/v1/admin/books/{id}/approve`
- [ ] POST `/api/v1/admin/books/{id}/reject`
- [ ] GET `/api/v1/admin/orders`
- [ ] GET `/api/v1/admin/withdrawals`
- [ ] POST `/api/v1/admin/withdrawals/{id}/approve`
- [ ] GET `/api/v1/admin/settings`
- [ ] PATCH `/api/v1/admin/settings`

### Blog
- [ ] GET `/api/v1/blog/posts`
- [ ] GET `/api/v1/blog/posts/{slug}`
- [ ] POST `/api/v1/blog/posts` (admin)

### Notifications
- [ ] GET `/api/v1/notifications`
- [ ] PATCH `/api/v1/notifications/{id}/read`

### Sitemap
- [ ] GET `/api/v1/sitemap/books`
- [ ] GET `/api/v1/sitemap/authors`
- [ ] GET `/api/v1/sitemap/categories`
- [ ] GET `/api/v1/sitemap/blog`

## 5. Celery Tasks

- [ ] `watermark_pdf` — kitobni watermark bilan tayyorlash
- [ ] `send_email` — email yuborish
- [ ] `expire_pending_orders` — 30 daqiqadan keyin
- [ ] `sync_book_to_meilisearch`
- [ ] `generate_demo_pdf` — birinchi 10 sahifa
- [ ] `process_avatar` — image resize
- [ ] `daily_backup` — DB backup (beat)
- [ ] `ping_search_engines` — yangi kontent

## 6. Frontend (Nuxt 3) — Sahifalar

### Asosiy
- [ ] `/` — Bosh sahifa
- [ ] `/catalog` — Katalog
- [ ] `/books/[slug]` — Kitob batafsil
- [ ] `/categories/[slug]` — Kategoriya
- [ ] `/authors` — Mualliflar ro'yxati
- [ ] `/authors/[slug]` — Muallif profili
- [ ] `/search` — Qidiruv natijalari
- [ ] `/blog` — Blog
- [ ] `/blog/[slug]` — Blog post

### Auth
- [ ] `/auth/login`
- [ ] `/auth/register`
- [ ] `/auth/forgot-password`
- [ ] `/auth/reset-password`
- [ ] `/auth/verify-email`

### Foydalanuvchi
- [ ] `/profile` — Sozlamalar
- [ ] `/profile/orders` — Buyurtmalarim
- [ ] `/profile/library` — Mening kitoblarim
- [ ] `/profile/wishlist` — Sevimlilar

### Muallif kabineti
- [ ] `/author/dashboard`
- [ ] `/author/books` — Mening kitoblarim
- [ ] `/author/books/new` — Yangi kitob
- [ ] `/author/books/[id]/edit` — Tahrirlash
- [ ] `/author/analytics` — Statistika
- [ ] `/author/withdrawals` — Pul olish
- [ ] `/author/profile` — Muallif profili

### Admin panel
- [ ] `/admin/dashboard`
- [ ] `/admin/users`
- [ ] `/admin/books`
- [ ] `/admin/books/moderation`
- [ ] `/admin/categories`
- [ ] `/admin/orders`
- [ ] `/admin/withdrawals`
- [ ] `/admin/blog`
- [ ] `/admin/settings`

### Checkout
- [ ] `/cart`
- [ ] `/checkout`
- [ ] `/checkout/success`
- [ ] `/checkout/failed`

### Statik
- [ ] `/about`
- [ ] `/contact`
- [ ] `/terms`
- [ ] `/privacy`
- [ ] `/offer`
- [ ] `/faq`
- [ ] `/404` (custom)
- [ ] `/500` (custom)

## 7. Frontend — Komponentlar

### Layout
- [ ] `AppHeader.vue`
- [ ] `AppFooter.vue`
- [ ] `MobileMenu.vue`
- [ ] `LanguageSwitcher.vue`
- [ ] `ThemeToggle.vue`

### Common
- [ ] `Button.vue` (variantlar)
- [ ] `Input.vue`
- [ ] `Textarea.vue`
- [ ] `Select.vue`
- [ ] `Checkbox.vue`
- [ ] `Modal.vue`
- [ ] `Drawer.vue`
- [ ] `Toast.vue`
- [ ] `Badge.vue`
- [ ] `Spinner.vue`
- [ ] `Skeleton.vue`
- [ ] `Breadcrumbs.vue`
- [ ] `Pagination.vue`
- [ ] `Tabs.vue`
- [ ] `EmptyState.vue`

### Book
- [ ] `BookCard.vue` (grid)
- [ ] `BookCardList.vue` (list view)
- [ ] `BookCover.vue`
- [ ] `BookPriceTag.vue`
- [ ] `BookRating.vue`
- [ ] `BookActions.vue` (buy, wishlist, share)
- [ ] `BookGallery.vue`
- [ ] `BookDescription.vue` (with read more)
- [ ] `BookSimilarBooks.vue`

### Author
- [ ] `AuthorCard.vue`
- [ ] `AuthorBio.vue`
- [ ] `AuthorStats.vue`

### Review
- [ ] `ReviewCard.vue`
- [ ] `ReviewForm.vue`
- [ ] `ReviewList.vue`
- [ ] `StarRating.vue`

### Checkout
- [ ] `CartItem.vue`
- [ ] `OrderSummary.vue`
- [ ] `PaymentMethods.vue`

### Admin
- [ ] `AdminSidebar.vue`
- [ ] `AdminDataTable.vue`
- [ ] `AdminStatsCard.vue`

## 8. Funksionallik

### Avtorizatsiya
- [ ] Email + parol bilan ro'yxatdan o'tish
- [ ] Email tasdiqlash
- [ ] Parolni unutdim flow
- [ ] JWT access/refresh tokenlar
- [ ] Auto-refresh interceptor (axios)
- [ ] Logout barcha qurilmalardan

### Kitob
- [ ] Muallif kitob yuklay oladi (PDF + cover)
- [ ] Demo PDF avtomatik generatsiya (10 sahifa)
- [ ] Kitob status: draft → review → published
- [ ] Admin moderatsiya
- [ ] Kategoriya tayinlash
- [ ] Til belgilash (uz/ru/en)
- [ ] Narx + bepul opsiya
- [ ] ISBN (ixtiyoriy)

### Qidiruv
- [ ] Meilisearch full-text
- [ ] Filter: kategoriya, til, narx, muallif
- [ ] Sort: yangi, narx (osc/desc), reyting, mashhur
- [ ] Pagination yoki infinite scroll

### Cart va to'lov
- [ ] Cart (localStorage)
- [ ] Checkout flow
- [ ] Payme integratsiya
- [ ] Order status track
- [ ] Library'ga avtomatik qo'shilish

### PDF
- [ ] Demo PDF.js viewer
- [ ] Watermark (foydalanuvchi email + sana)
- [ ] Signed URL download (24 soat)
- [ ] Sahifa raqamlari watermark

### Sharhlar
- [ ] Faqat sotib olganlar sharh yoza oladi
- [ ] 5 yulduzli reyting
- [ ] Admin moderatsiya
- [ ] Avtomatik o'rtacha reyting hisoblash

### Bildirishnomalar
- [ ] In-app (header'da qo'ng'iroq icon)
- [ ] Email: yangi sotuv (muallif), kitob mavjud (xaridor)
- [ ] Email: withdrawal status
- [ ] Telegram bot (ixtiyoriy, Phase 2)

### Muallif statistikasi
- [ ] Jami sotuv soni
- [ ] Jami daromad
- [ ] Top kitoblar
- [ ] Oylik grafik
- [ ] Withdrawal tarixi

## 9. Tarjima va lokallashtirish

- [ ] uz.json to'liq
- [ ] ru.json to'liq
- [ ] en.json to'liq
- [ ] Sana formati lokalga moslangan
- [ ] Narx formati so'm (UZS), juda kerak bo'lsa USD
- [ ] hreflang teglar har sahifada

## 10. Theme va UI

- [ ] Light mode
- [ ] Dark mode
- [ ] System auto
- [ ] Toggle 3-holat tugma
- [ ] CSS variables to'liq
- [ ] Mobile responsive (test: iPhone SE, iPhone 14, iPad)
- [ ] Tablet responsive

## 11. SEO

- [ ] Meta teglar har sahifada
- [ ] Title — noyob har sahifa uchun
- [ ] Description — noyob
- [ ] Open Graph
- [ ] Twitter Card
- [ ] JSON-LD: Book, Person, Organization, BreadcrumbList, FAQPage
- [ ] sitemap.xml dinamik
- [ ] robots.txt
- [ ] canonical URL
- [ ] hreflang
- [ ] Google Search Console
- [ ] Yandex Webmaster
- [ ] OG rasm dinamik

## 12. Performance

- [ ] PageSpeed mobile: 80+
- [ ] PageSpeed desktop: 90+
- [ ] LCP < 2.5s
- [ ] FID < 100ms
- [ ] CLS < 0.1
- [ ] Image lazy load
- [ ] WebP rasmlar
- [ ] Code splitting
- [ ] Brotli/gzip
- [ ] Redis cache
- [ ] CDN (Cloudflare yoki BunnyCDN)

## 13. Xavfsizlik

- [ ] HTTPS (Let's Encrypt)
- [ ] Rate limiting (IP, user)
- [ ] CSRF himoya (cookie based requests'da)
- [ ] XSS himoya (input sanitize)
- [ ] SQL injection himoya (ORM)
- [ ] CORS aniq
- [ ] HSTS header
- [ ] CSP header
- [ ] Password bcrypt (12 rounds)
- [ ] JWT secret key kuchli (32+ random)
- [ ] DB faqat ichki network'da
- [ ] MinIO buckets private (kitoblar)
- [ ] File upload validatsiya (PDF only, 100MB max)
- [ ] Virus scan (ClamAV, ixtiyoriy)

## 14. Tests

- [ ] Backend pytest: 60%+ coverage
- [ ] Frontend Vitest: asosiy komponentlar
- [ ] E2E Playwright: register → buy → download flow
- [ ] Load test: 100 RPS bardosh

## 15. Deploy

- [ ] Production `.env` to'liq
- [ ] SSL ishlaydi
- [ ] Domain yo'naltirilgan
- [ ] Backup cron job
- [ ] Monitoring (UptimeRobot)
- [ ] Error tracking (Sentry)
- [ ] Log aggregation
- [ ] DB backup test (qaytarib tiklash)

## 16. Legal

- [ ] Foydalanish shartlari (Terms of Service)
- [ ] Maxfiylik siyosati (Privacy Policy)
- [ ] Oferta (Public Offer)
- [ ] Mualliflik shartnomasi (Author Agreement)
- [ ] Cookie banner (ixtiyoriy)
- [ ] DMCA / copyright takedown jarayoni

## 17. Analytics

- [ ] Google Analytics 4
- [ ] Yandex Metrika
- [ ] Event tracking (register, buy, download)
- [ ] Conversion goals

## 18. Marketing tayyorgarligi

- [ ] Logo final versiyada
- [ ] Brand assets (favicon, OG default image)
- [ ] 5+ demo kitoblar yuklangan
- [ ] 2+ demo mualliflar profili tayyor
- [ ] 3+ blog post yozilgan
- [ ] Telegram kanal yaratilgan
- [ ] Facebook sahifa
- [ ] Instagram akkaunt
- [ ] Email shablon (Mailgun, SendGrid, yoki self-hosted)

## 19. Documentation

- [ ] README.md
- [ ] API documentation (`/docs` swagger)
- [ ] Frontend setup guide
- [ ] Backend setup guide
- [ ] Deployment guide
- [ ] Database schema diagram
- [ ] Troubleshooting / FAQ for developers

## 20. Final pre-launch

- [ ] Beta foydalanuvchilardan feedback olingan
- [ ] Critical buglar yo'q
- [ ] Backup amalda test qilingan
- [ ] Rollback rejasi tayyor
- [ ] Team xabardor
- [ ] Launch e'lon matni tayyor (Telegram, social media)
- [ ] Press release tayyor (mahalliy IT bloglar uchun)

---

## Yakuniy belgilash

Hammasi `[x]` bo'lganda — siz launch'ga tayyorsiz!

**Birinchi haftadagi maqsadlar:**
- 50+ foydalanuvchi ro'yxatdan o'tishi
- 5+ mualliflar kitob yuklashi
- 10+ kitob nashr qilinishi
- 5+ to'lov amalga oshirilishi

**Birinchi oydagi maqsadlar:**
- 500+ foydalanuvchi
- 30+ kitob
- 100+ tranzaksiya
- 100K+ so'm umumiy aylanma

---

**Maslahat:** Bu checklistni Notion yoki Trello'ga ko'chiring, har bir punkt uchun deadline qo'ying va kuniga progresni tekshiring. Omad!

---

Bosh sahifaga qaytish: [README](../README.md)
