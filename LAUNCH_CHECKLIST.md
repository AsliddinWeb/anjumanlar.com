# Launch checklist — monografiya.com

Saytni jamoatga ochishdan oldin shu ro'yxatdan o'ting. Har bandning
yon tomonidagi katakni qo'lda belgilang (`[ ]` → `[x]`).

Yo'riqnomalar:
- Deploy: [DEPLOY.md](./DEPLOY.md)
- Tarix: [CHANGELOG.md](./CHANGELOG.md)

---

## 1. Infrastruktura

- [ ] Server hozir (Ubuntu 22.04+ tavsiya etiladi)
- [ ] Docker + Compose v2 plugin o'rnatilgan (`docker compose version`)
- [ ] `deploy` foydalanuvchisi `docker` guruhida (`groups deploy | grep docker`)
- [ ] `/opt/monografiya.com` egasi `deploy`
- [ ] Repo klonlangan: `git clone https://github.com/AsliddinWeb/monografiya.com.git`
- [ ] Boshqa Docker loyihalar `83xx` portlarni band qilmayotgani tekshirilgan

## 2. DNS

3 ta A yozuvi server IP'siga ko'rsatishi kerak:

- [ ] `monografiya.com` → server IP
- [ ] `www.monografiya.com` → server IP
- [ ] `files.monografiya.com` → server IP (MinIO presigned URL'lar uchun)

Tekshirish: `dig +short monografiya.com www.monografiya.com files.monografiya.com`.

## 3. `.env` to'g'ri to'ldirilganmi

`.env.prod.example` ni `.env` ga ko'chiring va quyidagilarni to'ldiring:

- [ ] `POSTGRES_PASSWORD` (kuchli parol, `DATABASE_URL[_SYNC]` ichida ham yangilang)
- [ ] `MINIO_ROOT_PASSWORD` (kuchli parol)
- [ ] `MEILISEARCH_MASTER_KEY` (≥32 belgi)
- [ ] `JWT_SECRET_KEY` (generatsiya: `openssl rand -hex 32`)
- [ ] `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` — Brevo/Resend/Mailgun/SES
- [ ] `EMAIL_FROM` (`noreply@monografiya.com`) va `EMAIL_FROM_NAME`
- [ ] `MINIO_PUBLIC_ENDPOINT=https://files.monografiya.com`
- [ ] `NUXT_PUBLIC_API_BASE=https://monografiya.com/api/v1`
- [ ] `NUXT_PUBLIC_SITE_URL=https://monografiya.com`
- [ ] `FRONTEND_URL=https://monografiya.com`
- [ ] `CORS_ORIGINS=https://monografiya.com,https://www.monografiya.com`

Sentry (ixtiyoriy, tavsiya etiladi):

- [ ] `SENTRY_DSN` (backend proyekt)
- [ ] `NUXT_PUBLIC_SENTRY_DSN` (frontend proyekt)

Payme (sizda bo'lganda):

- [ ] `PAYME_MERCHANT_ID`
- [ ] `PAYME_SECRET_KEY` (webhook Basic Auth paroli)
- [ ] `PAYME_CHECKOUT_URL=https://checkout.paycom.uz` (sandbox emas)

## 4. Birinchi build + migration

- [ ] `make prod-build` (5-10 daqiqa, image'lar yig'iladi)
- [ ] `make prod-up`
- [ ] `make prod-migrate` (alembic upgrade head)
- [ ] `make prod-seed` (10 ta kategoriya)
- [ ] Konteynerlar holati: `make prod-ps` → barchasi `Up`/`healthy`

## 5. SSL sertifikat

```bash
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot --webroot-path=/var/www/certbot \
    --email you@monografiya.com --agree-tos --no-eff-email \
    -d monografiya.com -d www.monografiya.com -d files.monografiya.com
```

- [ ] Sertifikat olindi (`/etc/letsencrypt/live/monografiya.com/`)
- [ ] `nginx/conf.d/monografiya.com.conf` ga `listen 443 ssl` bloki qo'shildi
- [ ] `docker compose -f docker-compose.prod.yml exec nginx nginx -s reload`
- [ ] HTTPS ishlamoqda: `curl -I https://monografiya.com`
- [ ] Certbot auto-renewal konteyneri ishlamoqda (`make prod-ps | grep certbot`)

## 6. Birinchi superadmin

- [ ] `make prod-create-admin EMAIL=you@monografiya.com PASSWORD='Strong!2026' NAME='Site Admin'`
- [ ] Login tekshirildi: <https://monografiya.com/uz/auth/login>
- [ ] Header dropdown'da "⚙ Admin panel" linki ko'rinmoqda
- [ ] `/uz/admin` KPI dashboard ochiladi (boshlang'ich barcha sonlar 0 yoki seed darajada)

## 7. Funksional smoke test

Browser'da real foydalanuvchi sifatida:

- [ ] Bosh sahifa yuklanadi, til o'tkazgich ishlaydi (uz/ru/en)
- [ ] `/books` katalog 200, filterlar URL'ga sinxronlanadi
- [ ] Kitob detal sahifasi (`/books/{slug}`), demo PDF ochiladi (agar mavjud bo'lsa)
- [ ] Ro'yxatdan o'tish → email keladi (MailHog yoki haqiqiy SMTP)
- [ ] Email tasdiqlash linki ishlaydi
- [ ] Login → header'da foydalanuvchi nomi ko'rinadi
- [ ] Sevimliga qo'shish, savatga qo'shish ishlaydi (localStorage)
- [ ] Mobile drawer (≤768px) ochiladi va navigatsiya ishlaydi
- [ ] Skip-to-content linki Tab bilan ko'rinadi
- [ ] 404 sahifasi tushgan slug uchun: <https://monografiya.com/uz/yoq-bunday>

## 8. Admin oqimlari

Admin sifatida:

- [ ] `/admin/books` pending kitoblar ko'rinadi (yoki bo'sh empty state)
- [ ] Approve/Reject tugmalari ishlaydi
- [ ] `/admin/categories` — yangi kategoriya yaratib o'chirish
- [ ] `/admin/users` — search + role/status filter ishlaydi
- [ ] `/admin/blog` — yangi post yaratib publish qilish, `/uz/blog` da ko'rinadi
- [ ] `/admin/audit` — login_success yozuvi ko'rinadi
- [ ] `/admin/stats` endpoint javob qaytaradi (curl orqali)

## 9. SEO + indexing

- [ ] `https://monografiya.com/robots.txt` ochiladi va `Sitemap:` qatori bor
- [ ] `https://monografiya.com/sitemap.xml` valid XML, URL'lar ro'yxati
- [ ] Bosh sahifa `view-source:` da `<meta og:*>`, hreflang link'lar bor
- [ ] Kitob sahifasida `<script type="application/ld+json">` Book schema bor
- [ ] Google Search Console'da sayt qo'shildi va sitemap submit qilindi
- [ ] Bing Webmaster Tools'da ham qo'shildi (ixtiyoriy)

## 10. Payme integratsiyasi (sandbox/production)

- [ ] Payme dashboard'da webhook URL sozlangan: `https://monografiya.com/api/v1/payments/payme/webhook`
- [ ] Test sotib olish — 1000 so'mlik kitob bilan haqiqiy test (kichik summa)
- [ ] Webhook backend log'ida ko'rinadi: `make prod-logs s=backend | grep payme`
- [ ] Sotib olingach foydalanuvchi `email_paid` + `library_grant` emaillarni oladi
- [ ] Kitob `/account/library` da ko'rinadi va PDF yuklab olinadi

## 11. Monitoring

Sentry ulanganda:

- [ ] Backend init log'ida `Sentry initialised env=production` chiqdi
- [ ] Frontend bundle'da `@sentry/vue` yuklangan (browser DevTools Network)
- [ ] Test xato Sentry'ga keldi-yi (masalan, fake `/api/v1/error-test` chaqirig'i)

Logs:

- [ ] `make prod-logs s=backend` 5xx xato bermayapti
- [ ] `make prod-logs s=celery_worker` task'lar bajarilmoqda
- [ ] `make prod-logs s=celery_beat` `orders.expire_pending` chaqirilmoqda (har daqiqada)

## 12. Backup

- [ ] `make prod-backup` qo'lda muvaffaqiyatli o'tdi
- [ ] `/var/backups/monografiya/<TS>/` ichida `postgres.dump.gz` va `minio_data.tar.gz` bor
- [ ] Cron yozuvi `/etc/cron.d/monografiya-backup` o'rnatildi
- [ ] Cron muvaffaqiyat log'iga yozadi: `cat /var/log/monografiya-backup.log`
- [ ] Off-site rsync sozlandi (`rclone`, AWS S3, va h.k.) — **muhim**

## 13. Performance + xavfsizlik

- [ ] Lighthouse audit `/` sahifasi uchun: Performance ≥ 80, SEO ≥ 90, A11y ≥ 90
- [ ] `ssl-labs.com/ssltest` natijasi A yoki A+
- [ ] `securityheaders.com` natijasi B+ yoki yuqori
- [ ] `JWT_SECRET_KEY` va boshqa `change-me-*` qiymatlar tugatilmagan
- [ ] `.env` fayli `chmod 600 deploy` ostida, `git status` da ko'rinmaydi
- [ ] Backend admin panelda `noindex` ekanini Google'da tekshirish

## 14. Yuridik + kontent

- [ ] `/legal/terms` va `/legal/privacy` to'liq matnlar bilan to'ldirilgan
  (draft placeholderlardan voz kechilgan)
- [ ] Telegram link footer'da to'g'ri: `https://t.me/monografiya`
- [ ] `info@monografiya.com` pochta qutisi ishlamoqda
- [ ] Bosh sahifaning "Become an author" CTA testlandi (`/authors/me`)

## 15. Launch kuni

- [ ] DNS uzgartirishlar 24 soat oldin amalga oshirildi
- [ ] `make prod-deploy` oxirgi marotaba bajarildi (latest commit)
- [ ] Smoke testning yana bir martabasi (10–12 bo'limlar)
- [ ] Birinchi e'lon: Telegram, ijtimoiy tarmoqlar
- [ ] Birinchi 1-2 soat ichida Sentry + log'larni kuzatish
- [ ] Birinchi sotib olishni nazoratga olish, Payme webhook'i to'g'ri ishlamoqdami

---

## Launch'dan keyin

- [ ] 1-hafta: kunlik log audit, Sentry top error'larini tuzatish
- [ ] 1-oy: foydalanuvchilardan feedback yig'ish, blog'da birinchi maqola
- [ ] 3-oy: Phase 8 rejasi — `@nuxtjs/seo` migratsiyasi, blog kategoriyalari,
  subscription model, va h.k. (doc'da yozilgan)
