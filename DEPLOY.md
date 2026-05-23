# Deploy yo'riqnomasi — anjumanlar.com

Server: `deploy@academicbook`, joylashuv: `/opt/anjumanlar.com`.

Domain: `anjumanlar.com` va `www.anjumanlar.com`.

Docker barcha servislarni boshqaradi (nginx, postgres, redis, minio,
meilisearch, backend, frontend, celery worker + beat). Faqat `80/443`
port'lar host'ga ochiq — qolganlari `127.0.0.1:<8300+>` da
internal'da turadi.

---

## 1. Birinchi marta o'rnatish

### 1.1 Server tayyorgarligi

```bash
# Docker + compose plugin (debian/ubuntu).
sudo apt update && sudo apt install -y docker.io docker-compose-plugin

# deploy foydalanuvchini docker guruhiga qo'shing.
sudo usermod -aG docker deploy
# qayta login qiling
```

### 1.2 Loyihani klonlash

```bash
cd /opt
sudo mkdir -p anjumanlar.com
sudo chown deploy:deploy anjumanlar.com
cd anjumanlar.com
git clone https://github.com/AsliddinWeb/anjumanlar.com.git .
```

### 1.3 `.env` faylini tayyorlash

```bash
cp .env.prod.example .env
# Quyidagilarni real qiymatlar bilan to'ldiring (vim/nano):
#   POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, JWT_SECRET_KEY,
#   MEILISEARCH_MASTER_KEY, SMTP_* (Brevo/Resend/...), 
#   PAYME_* (hozircha bo'sh qoldiring)
nano .env

# JWT kalitini xavfsiz generatsiya qilish:
openssl rand -hex 32
```

### 1.4 Birinchi build + ishga tushirish

```bash
# Image'larni yig'ish (5-10 daqiqa).
docker compose -f docker-compose.prod.yml build

# Servislarni ko'tarish (nginx, frontend, backend va h.k.).
docker compose -f docker-compose.prod.yml up -d

# Migration'larni qo'llash.
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Kategoriyalar seed (10 ta kategoriya).
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.seed_categories
```

### 1.5 SSL sertifikatini olish

3 ta DNS A yozuvi sozlangan bo'lishi kerak (hammasi server IP'siga):

```
anjumanlar.com         A   <server-ip>
www.anjumanlar.com     A   <server-ip>
files.anjumanlar.com   A   <server-ip>
```

`files.anjumanlar.com` — MinIO presigned URL'lar uchun alohida subdomen
(kitob muqovalari, demo PDF'lar, watermarked nusxalar shu yerda).

Tekshirish:

```bash
dig +short anjumanlar.com
dig +short www.anjumanlar.com
dig +short files.anjumanlar.com
```

Sertifikat olish (certbot Docker container ichida ishlaydi):

```bash
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@anjumanlar.com \
    --agree-tos \
    --no-eff-email \
    -d anjumanlar.com \
    -d www.anjumanlar.com \
    -d files.anjumanlar.com
```

> **Eslatma:** certbot HTTP-01 challenge ishlatadi —
> `/.well-known/acme-challenge/` yo'li nginx config'ida ochiq.

Sertifikat olingach `nginx/conf.d/anjumanlar.com.conf` ga HTTPS bloki
qo'shing (oxiriga):

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name anjumanlar.com www.anjumanlar.com;

    ssl_certificate     /etc/letsencrypt/live/anjumanlar.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/anjumanlar.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... va listen 80 bloki bilan bir xil location'lar (yoki "include")
}
```

Yoki oson yo'l — `certbot --nginx` qo'shimcha `--installer nginx`'siz
ishlamasdan, qo'lda yozish kerak. Sertifikat avto-yangilanishi
`certbot` servisi orqali bo'ladi (12 soatda bir marta tekshiradi).

Nginx'ni reload qilish:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 1.6 Birinchi superadmin yaratish

`POST /auth/register` doim `role=reader` qaytaradi (xavfsizlik uchun).
Birinchi admin'ni quyidagi bootstrap script orqali yarating:

```bash
docker compose -f docker-compose.prod.yml exec backend \
    python -m app.scripts.create_admin \
    --email you@anjumanlar.com \
    --password 'StrongPass!2026' \
    --name 'Site Admin'
```

Yoki Makefile orqali:

```bash
make prod-create-admin \
    EMAIL=you@anjumanlar.com \
    PASSWORD='StrongPass!2026' \
    NAME='Site Admin'
```

Script idempotent — agar shu email allaqachon mavjud bo'lsa (masalan,
saytda ro'yxatdan o'tgan bo'lsangiz), uni `superadmin` ga ko'taradi va
`email_verified=true`, `status=active` qiladi. Parolni o'zgartirish
uchun `--reset-password` flag qo'shing.

Endi `https://anjumanlar.com/uz/auth/login` orqali kirib, header'dagi
user dropdown'dan **⚙ Admin panel** linki orqali `/uz/admin` ga
o'tasiz.

### 1.7 Holatni tekshirish

```bash
# Konteynerlar:
docker compose -f docker-compose.prod.yml ps

# Backend ping:
curl https://anjumanlar.com/api/v1/ping
# {"pong":"ok"}

# Frontend bosh sahifa:
curl -I https://anjumanlar.com
# HTTP/2 200
```

---

## 2. Keyingi safar deploy qilish

Yangi commit kelganda yoki kichik o'zgarish bo'lganda:

```bash
cd /opt/anjumanlar.com
./scripts/deploy.sh
```

Script:
1. `git pull --ff-only` qiladi
2. Docker image'larni qayta yig'adi
3. Servislarni qayta ko'taradi
4. Migration'larni qo'llaydi
5. Kategoriyalarni seed qiladi (idempotent — mavjudlarini o'tkazib yuboradi)
6. Nginx config'ni reload qiladi

---

## 3. Foydali komandalar

```bash
# Loglarni ko'rish:
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx

# Backend ichiga kirish (psql + shell):
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec postgres psql -U anjumanlar

# Faqat bitta servisni restart:
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart nginx

# To'liq to'xtatish:
docker compose -f docker-compose.prod.yml down
# To'liq tozalash (volumes bilan — DIQQAT, ma'lumotlar o'chiriladi):
docker compose -f docker-compose.prod.yml down -v
```

---

## 4. Payme'ni keyinchalik yoqish

Merchant credentials kelganda:

```bash
# .env'ni yangilash:
sed -i 's/^PAYME_MERCHANT_ID=.*/PAYME_MERCHANT_ID=your-merchant-id/' .env
sed -i 's/^PAYME_SECRET_KEY=.*/PAYME_SECRET_KEY=your-secret-key/' .env

# Production checkout URL ga o'zgartirish (sandbox emas):
sed -i 's|^PAYME_CHECKOUT_URL=.*|PAYME_CHECKOUT_URL=https://checkout.paycom.uz|' .env

# Backend va worker'ni restart (env_file qayta o'qiladi):
docker compose -f docker-compose.prod.yml restart backend celery_worker celery_beat
```

Payme dashboard'da webhook URL'ni sozlang:

```
https://anjumanlar.com/api/v1/payments/payme/webhook
```

Basic Auth username = `Paycom`, parol = `PAYME_SECRET_KEY` qiymatiga teng.

---

## 5. Sentry (xato monitoringi)

Backend va frontend uchun **ikkita alohida** Sentry projecti yarating
(odatda "Anjumanlar Backend" + "Anjumanlar Frontend"). Har birining
DSN'ini `.env`'ga qo'ying:

```bash
# Backend
SENTRY_DSN=https://...@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=production

# Frontend (browser SDK alohida)
NUXT_PUBLIC_SENTRY_DSN=https://...@o0.ingest.sentry.io/0
NUXT_PUBLIC_SENTRY_ENVIRONMENT=production
```

So'ng:

```bash
docker compose -f docker-compose.prod.yml up -d backend frontend
```

Init loglarini tekshirish:

```bash
docker compose -f docker-compose.prod.yml logs backend | grep "Sentry"
# Sentry initialised env=production
```

DSN bo'sh bo'lsa init no-op qiladi — sayt ishlayveradi.

---

## 6. Backup va restore

Repo'da `scripts/backup.sh` va `scripts/restore.sh` tayyor — ikkalasi
ham PostgreSQL'ni `pg_dump` orqali va MinIO volume'ini `tar.gz` orqali
saqlaydi. Backup default 30 kun saqlanadi (`BACKUP_RETENTION_DAYS`).

### Qo'lda ishga tushirish

```bash
cd /opt/anjumanlar.com
make prod-backup
# Yoki to'g'ridan-to'g'ri: ./scripts/backup.sh
```

Natijada `/var/backups/anjumanlar/YYYYMMDD-HHMMSS/` ichida ikkita fayl
paydo bo'ladi:

- `postgres.dump.gz` — `pg_dump --format=custom` (pg_restore bilan ochiladi)
- `minio_data.tar.gz` — MinIO volume'ining to'liq snapshot'i

### Kunlik cron

```bash
sudo install -m 644 /dev/stdin /etc/cron.d/anjumanlar-backup <<'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Har kuni 03:15 da
15 3 * * * deploy /opt/anjumanlar.com/scripts/backup.sh >> /var/log/anjumanlar-backup.log 2>&1
EOF
```

Backup loglarini `/var/log/anjumanlar-backup.log` faylida kuzatasiz.

### Restore

```bash
make prod-restore BACKUP=/var/backups/anjumanlar/20260801-030000
```

`users` jadvali bo'sh emasligini bilsa, script ishni to'xtatadi. Buni
o'tkazib yuborish uchun:

```bash
make prod-restore BACKUP=/var/backups/anjumanlar/20260801-030000 FORCE=1
```

Restore'dan keyin migration'larni qayta qo'llang (yangi commit'larda
keyingi migration bo'lishi mumkin):

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml restart backend celery_worker celery_beat
```

### Saqlash joyini boshqa volume'ga ko'chirish

Defolt `/var/backups`. O'zgartirish uchun cron qatorida `BACKUP_DIR`
ni ko'rsating:

```cron
15 3 * * * deploy BACKUP_DIR=/mnt/backup-disk /opt/anjumanlar.com/scripts/backup.sh
```

Off-site saqlash uchun bu papkani `rsync`/`rclone` orqali keyin uzoq
serverga ko'chirish tavsiya etiladi.
