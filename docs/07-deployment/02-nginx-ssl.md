# Nginx + SSL (Let's Encrypt)

Production'da Nginx — reverse proxy. SSL — Let's Encrypt orqali bepul.

## docker/nginx/nginx.conf

```nginx
user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Basic
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 4096;
    server_tokens off;
    
    client_max_body_size 150M;  # Kitob fayllari uchun
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript 
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml application/font-woff2;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/s;

    # SSL global
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Includes
    include /etc/nginx/conf.d/*.conf;
}
```

## docker/nginx/conf.d/monografiya.conf

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name monografiya.com www.monografiya.com;

    # Certbot ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# www → non-www
server {
    listen 443 ssl http2;
    server_name www.monografiya.com;

    ssl_certificate /etc/nginx/ssl/live/monografiya.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/monografiya.com/privkey.pem;

    return 301 https://monografiya.com$request_uri;
}

# Asosiy HTTPS server
server {
    listen 443 ssl http2;
    server_name monografiya.com;

    # SSL
    ssl_certificate /etc/nginx/ssl/live/monografiya.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/monografiya.com/privkey.pem;
    ssl_trusted_certificate /etc/nginx/ssl/live/monografiya.com/chain.pem;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    
    # Xavfsizlik headerlari
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # CSP — frontend ehtiyojiga qarab sozlanadi
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.paycom.uz; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' https://api.monografiya.com; frame-src https://checkout.paycom.uz;" always;

    # Backend API
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;
        
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    # Auth endpoints — yanada qattiq rate limit
    location ~ ^/api/v1/auth/(login|register|forgot-password|reset-password) {
        limit_req zone=auth_limit burst=10 nodelay;
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Payme webhook — alohida
    location = /api/v1/payments/payme/webhook {
        limit_req zone=webhook_limit burst=20 nodelay;
        
        # Payme IP'lari uchun whitelist (ixtiyoriy)
        # allow 185.234.113.0/24;
        # deny all;
        
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # MinIO public — covers/avatars/blog
    location ~ ^/static/(covers|avatars|blog|demos)/ {
        rewrite ^/static/(.*)$ /$1 break;
        proxy_pass http://minio:9000;
        proxy_set_header Host $host;
        
        # Cache statika
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend (Nuxt SSR)
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Nuxt static assets
    location /_nuxt/ {
        proxy_pass http://frontend:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## SSL — Let's Encrypt boshlang'ich sozlash

### 1. DNS ni tekshirish

Saytingiz IP manzilingizga `A` recordi orqali ulangan bo'lishi kerak:
```
monografiya.com.        A    YOUR_SERVER_IP
www.monografiya.com.    A    YOUR_SERVER_IP
```

### 2. Vaqtinchalik nginx ishga tushirish (faqat HTTP)

`docker/nginx/conf.d/monografiya.conf`'ni vaqtincha o'zgartiring:

```nginx
server {
    listen 80;
    server_name monografiya.com www.monografiya.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 "OK";
    }
}
```

### 3. Sertifikat olish

```bash
# Nginx'ni ishga tushiring
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx

# Certbot'ni ishga tushiring
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@monografiya.com \
    --agree-tos \
    --no-eff-email \
    -d monografiya.com \
    -d www.monografiya.com
```

### 4. To'liq config'ga qaytib nginx restart

```bash
# To'liq nginx config'ni qaytaring (yuqoridagi)
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### 5. Avtomatik yangilash

Certbot servisi compose'da allaqachon yozilgan — har 12 soatda renew tekshiradi:

```yaml
certbot:
  image: certbot/certbot:latest
  volumes:
    - ./docker/nginx/ssl:/etc/letsencrypt
    - ./docker/nginx/certbot/www:/var/www/certbot
  entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

Sertifikat yangilangandan keyin nginx reload qiladigan cron qo'shing (host'da):

```bash
# crontab -e
0 */12 * * * docker compose -f /path/to/docker-compose.yml exec -T nginx nginx -s reload
```

## SSL test

```bash
# Sertifikatni tekshirish
curl -vI https://monografiya.com 2>&1 | grep -E '(SSL|TLS|HTTP)'

# Online test
# https://www.ssllabs.com/ssltest/
```

A+ baho olish uchun yuqorida ko'rsatilgan SSL sozlamalar yetarli.

## Diqqat

1. **Firewall** — server'da faqat 80, 443, 22 portlari ochiq bo'lsin:
   ```bash
   ufw allow 22
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

2. **DNS to'g'rilangani** — `dig monografiya.com` natijasi to'g'ri IP'ni ko'rsatishi kerak

3. **Rate limit yengilroq qiling, agar kerak bo'lsa** — yuqoridagi qiymatlar boshlang'ich

4. **Logs** — `/var/log/nginx/`'ni vaqti-vaqti bilan tekshiring

**Keyingi qadam:** `07-deployment/03-production-checklist.md`
