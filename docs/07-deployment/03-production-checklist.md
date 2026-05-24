# Production Checklist — Monografiya

Production'ga deploy qilishdan oldin barcha punktlarni tekshiring.

## 1. Server Setup

### Server talablari
- [ ] Ubuntu 22.04 LTS (yoki Debian 12)
- [ ] Minimum 4 GB RAM, 2 vCPU
- [ ] 50+ GB SSD disk
- [ ] Statik IP manzil
- [ ] Domain DNS sozlangan (`monografiya.com` → server IP)

### Server xavfsizligi
- [ ] SSH root login o'chirilgan (`PermitRootLogin no`)
- [ ] SSH faqat SSH key bilan (parol o'chirilgan)
- [ ] Standart SSH port o'zgartirilgan (22 → boshqa port)
- [ ] UFW firewall yoqilgan: faqat 22, 80, 443 ochiq
- [ ] `fail2ban` o'rnatilgan SSH bruteforce'dan himoya
- [ ] Sudo user yaratilgan, root o'rniga shu user ishlatiladi
- [ ] Avtomatik security updates yoqilgan (`unattended-upgrades`)

```bash
# UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## 2. Environment Variables

### `.env` fayl tekshiruvi
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` 32+ belgi, random generatsiya qilingan
- [ ] `JWT_SECRET_KEY` boshqa random key
- [ ] `POSTGRES_PASSWORD` kuchli parol
- [ ] `REDIS_PASSWORD` o'rnatilgan
- [ ] `MINIO_ROOT_PASSWORD` kuchli parol
- [ ] `MEILI_MASTER_KEY` o'rnatilgan
- [ ] `PAYME_MERCHANT_ID` va `PAYME_SECRET_KEY` production qiymatlar
- [ ] `CORS_ORIGINS` faqat `https://monografiya.com` (wildcard yo'q)
- [ ] `ALLOWED_HOSTS=monografiya.com,www.monografiya.com`
- [ ] SMTP credentials production email server

```bash
# Random key generatsiya
openssl rand -hex 32
```

### Sensitive fayllar
- [ ] `.env` faylga 600 permission (`chmod 600 .env`)
- [ ] `.env` git'ga qo'shilmagan (`.gitignore`'da bor)
- [ ] Backup'lar shifrlangan joyda saqlanadi

## 3. SSL / HTTPS

- [ ] Let's Encrypt sertifikat o'rnatilgan
- [ ] HTTP → HTTPS redirect ishlaydi
- [ ] `www.monografiya.com` → `monografiya.com` redirect
- [ ] HSTS header yoqilgan
- [ ] SSL Labs test natija: A yoki A+ (https://www.ssllabs.com/ssltest/)
- [ ] Certbot auto-renew sozlangan

## 4. Database

- [ ] PostgreSQL parol kuchli
- [ ] DB faqat ichki Docker network'dan kirish mumkin (port tashqariga ochiq emas)
- [ ] Avtomatik backup sozlangan (kuniga 1 marta)
- [ ] Backup'lar external storage'da (S3 yoki boshqa server)
- [ ] Backup'larni qayta tiklash test qilingan
- [ ] DB migration'lar (Alembic) bajarilgan: `alembic upgrade head`
- [ ] Seed data faqat zarur ma'lumotlar (demo userlar yo'q!)
- [ ] Indexlar yaratilgan (search, foreign keys)

```bash
# Backup cron
0 3 * * * /opt/monografiya/scripts/backup.sh
```

## 5. Backend (FastAPI)

- [ ] `DEBUG=False`
- [ ] Multiple workers ishlaydi (Gunicorn yoki Uvicorn workers=4)
- [ ] Health check endpoint mavjud: `/health`
- [ ] Rate limiting yoqilgan
- [ ] CORS to'g'ri sozlangan
- [ ] Error tracking (Sentry) sozlangan
- [ ] Logging: stdout → Docker logs → log aggregator
- [ ] API documentation production'da yopiq yoki himoyalangan (`/docs` faqat admin uchun)

```python
# main.py — production'da Swagger yashirish
app = FastAPI(
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
```

## 6. Frontend (Nuxt 3)

- [ ] Production build qilingan: `npm run build`
- [ ] `NUXT_PUBLIC_API_BASE` to'g'ri URL
- [ ] Google Analytics / Yandex Metrika qo'shilgan
- [ ] Favicon va manifest fayllar
- [ ] OpenGraph meta'lar har bir sahifada
- [ ] Sitemap.xml generatsiya qilinadi
- [ ] robots.txt to'g'ri
- [ ] 404 va 500 sahifalari yaratilgan
- [ ] Error tracking (Sentry) frontend uchun ham

## 7. File Storage (MinIO)

- [ ] MinIO production rejimda
- [ ] Bucket'lar yaratilgan: `books`, `books-watermarked`, `covers`, `demos`, `avatars`, `blog`
- [ ] `books` va `books-watermarked` PRIVATE
- [ ] `covers`, `avatars`, `blog` PUBLIC READ
- [ ] Disk space monitoring sozlangan
- [ ] Backup strategiyasi (MinIO Server-Side Replication yoki cron rsync)

## 8. Payment (Payme)

- [ ] Payme production credentials olingan
- [ ] Webhook URL Payme kabinetida ro'yxatdan o'tgan: `https://monografiya.com/api/v1/payments/payme/webhook`
- [ ] Webhook IP whitelist (Payme IP'lari)
- [ ] Test to'lov muvaffaqiyatli amalga oshirilgan
- [ ] Refund / cancel flow test qilingan
- [ ] Payment logs saqlanadi (audit uchun)

## 9. SEO va Analytics

- [ ] `robots.txt` to'g'ri
- [ ] `sitemap.xml` generatsiya qilinadi va Google Search Console'ga yuborildi
- [ ] Google Search Console'da domain tasdiqlangan
- [ ] Yandex Webmaster'da ham qo'shilgan
- [ ] Open Graph meta'lar test qilindi (Facebook Sharing Debugger)
- [ ] Twitter Card meta'lar test qilindi
- [ ] JSON-LD strukturalashtirilgan ma'lumotlar (Book, Person, Organization)
- [ ] `hreflang` teglar to'g'ri
- [ ] Google Analytics 4 sozlangan
- [ ] Yandex Metrika sozlangan (Uzbekistan auditoriyasi uchun)

## 10. Performance

- [ ] Nginx gzip yoqilgan
- [ ] Brotli compression (ixtiyoriy, undan ham yaxshi)
- [ ] Static fayllar cache: 1 yil
- [ ] CDN sozlangan (ixtiyoriy: Cloudflare)
- [ ] Image lazy loading
- [ ] PageSpeed Insights: 80+ mobile, 90+ desktop
- [ ] Database query'lar optimizatsiya qilingan (N+1 yo'q)
- [ ] Slow query log yoqilgan

## 11. Monitoring va Logging

- [ ] Server resurs monitoring: CPU, RAM, disk (Netdata, Grafana yoki Uptime Robot)
- [ ] Application monitoring (Sentry yoki self-hosted GlitchTip)
- [ ] Uptime monitoring (UptimeRobot, BetterStack, free tier)
- [ ] Alert'lar Telegram yoki email orqali keladi
- [ ] Log retention: 30 kun

## 12. Backup va Disaster Recovery

### Kuniga backup qilinishi kerak narsalar
- [ ] PostgreSQL database (`pg_dump`)
- [ ] MinIO buckets (`mc mirror`)
- [ ] Application config (`.env`, `docker-compose.yml`)

### Backup strategiyasi
- [ ] Local backup: `/var/backups/monografiya/` (7 kun)
- [ ] Remote backup: boshqa server yoki S3 (30 kun)
- [ ] Backup'larni test qilish (qaytarib tiklash) — oyiga bir marta

### `backup.sh` namuna
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/var/backups/monografiya"

# Database
docker exec monografiya_db pg_dump -U monografiya monografiya | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# MinIO
mc mirror /var/lib/docker/volumes/monografiya_minio_data $BACKUP_DIR/minio_$DATE/

# Old backuplarni o'chirish (7 kundan eski)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

# Remote'ga yuborish (rclone yoki rsync)
rclone copy $BACKUP_DIR remote:monografiya-backups/
```

## 13. Legal va Compliance

- [ ] Foydalanish shartlari (Terms of Service) sahifasi
- [ ] Maxfiylik siyosati (Privacy Policy) sahifasi
- [ ] Cookie banner (agar tracking ishlatilsa)
- [ ] Mualliflik shartnomasi (Author Agreement)
- [ ] Oferta (Public Offer) sahifasi
- [ ] DMCA / Copyright takedown jarayoni hujjatlashtirilgan

## 14. Final Tests

Production'ga ko'tarilgandan keyin tekshirish:

- [ ] Bosh sahifa yuklanadi: https://monografiya.com
- [ ] Ro'yxatdan o'tish ishlaydi
- [ ] Login ishlaydi
- [ ] Kitob ko'rish ishlaydi
- [ ] To'lov to'liq sikldan o'tadi
- [ ] PDF download ishlaydi
- [ ] Admin panel ishlaydi
- [ ] Muallif kabineti ishlaydi
- [ ] 3 til orasida o'tish ishlaydi
- [ ] Dark / light theme ishlaydi
- [ ] Email yuboriladi (registratsiya tasdiqlash)
- [ ] Mobile da yaxshi ko'rinadi
- [ ] Search ishlaydi

## 15. Launch

- [ ] DNS to'liq tarqalgan
- [ ] SSL ishlaydi
- [ ] Hamma checklistlar bajarilgan
- [ ] Backup tayyor (rollback uchun)
- [ ] Team xabardor
- [ ] Soft launch (beta foydalanuvchilar bilan)
- [ ] Bug feedback yig'ish
- [ ] Public launch e'lon qilish

---

**Keyingi qadam:** [Design System](../08-design/01-design-system.md)
