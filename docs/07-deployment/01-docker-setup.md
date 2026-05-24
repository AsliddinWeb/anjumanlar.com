# Docker Setup

Loyiha to'liq Docker Compose orqali ishlatiladi. Hech narsani lokal kompyuterga o'rnatishingiz shart emas (Docker'dan tashqari).

## Talab

- Docker 24+
- Docker Compose v2
- 4 GB RAM (minimum)

## Servislar ro'yxati

| Servis | Port | Ma'no |
|---|---|---|
| `frontend` | 3000 | Nuxt 3 SSR |
| `backend` | 8000 | FastAPI |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Cache + Celery broker |
| `minio` | 9000, 9001 | S3-compatible storage |
| `meilisearch` | 7700 | Full-text search |
| `celery_worker` | — | Background tasks |
| `celery_beat` | — | Scheduled tasks |
| `nginx` | 80, 443 | Reverse proxy (faqat prod) |
| `mailhog` | 1025, 8025 | Email testing (dev) |

## docker-compose.yml (development)

```yaml
name: monografiya

services:
  db:
    image: postgres:16-alpine
    container_name: monografiya-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-monografiya}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: monografiya-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redis}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-redis}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: monografiya-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Web UI
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 10s
      retries: 3

  minio-init:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin};
      mc mb --ignore-existing local/books;
      mc mb --ignore-existing local/books-watermarked;
      mc mb --ignore-existing local/covers;
      mc mb --ignore-existing local/demos;
      mc mb --ignore-existing local/avatars;
      mc mb --ignore-existing local/blog;
      mc anonymous set download local/covers;
      mc anonymous set download local/avatars;
      mc anonymous set download local/blog;
      mc anonymous set download local/demos;
      exit 0;
      "

  meilisearch:
    image: getmeili/meilisearch:v1.10
    container_name: monografiya-meilisearch
    restart: unless-stopped
    environment:
      MEILI_MASTER_KEY: ${MEILI_MASTER_KEY:-master_key_change_me}
      MEILI_ENV: development
    volumes:
      - meilisearch_data:/meili_data
    ports:
      - "7700:7700"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: monografiya-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    env_file:
      - ./backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-monografiya}
      REDIS_URL: redis://:${REDIS_PASSWORD:-redis}@redis:6379/0
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD:-redis}@redis:6379/1
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD:-redis}@redis:6379/2
      MINIO_ENDPOINT: minio:9000
      MEILISEARCH_HOST: http://meilisearch:7700
    volumes:
      - ./backend:/app  # Dev'da hot-reload
    ports:
      - "8000:8000"
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: monografiya-celery-worker
    restart: unless-stopped
    depends_on:
      - redis
      - db
    env_file:
      - ./backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-monografiya}
      REDIS_URL: redis://:${REDIS_PASSWORD:-redis}@redis:6379/0
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD:-redis}@redis:6379/1
      MINIO_ENDPOINT: minio:9000
    volumes:
      - ./backend:/app
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: monografiya-celery-beat
    restart: unless-stopped
    depends_on:
      - redis
    env_file:
      - ./backend/.env
    environment:
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD:-redis}@redis:6379/1
    volumes:
      - ./backend:/app
    command: celery -A app.celery_app beat --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: monografiya-frontend
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      API_BASE_URL: http://backend:8000/api/v1
      SITE_URL: http://localhost:3000
      NUXT_HOST: 0.0.0.0
      NUXT_PORT: 3000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    command: npm run dev

  mailhog:
    image: mailhog/mailhog:latest
    container_name: monografiya-mailhog
    restart: unless-stopped
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
  redis_data:
  minio_data:
  meilisearch_data:
```

## docker-compose.prod.yml (production override)

```yaml
name: monografiya

services:
  db:
    ports: []  # Don't expose externally
    
  redis:
    ports: []
  
  minio:
    ports:
      - "127.0.0.1:9001:9001"  # Console faqat localhost
  
  meilisearch:
    ports: []
    environment:
      MEILI_ENV: production
  
  backend:
    volumes: []  # Hot-reload yo'q
    ports:
      - "127.0.0.1:8000:8000"
    command: >
      sh -c "alembic upgrade head &&
             gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
  
  frontend:
    build:
      dockerfile: Dockerfile  # Production Dockerfile
    volumes: []
    ports:
      - "127.0.0.1:3000:3000"
    command: node .output/server/index.mjs
  
  nginx:
    image: nginx:alpine
    container_name: monografiya-nginx
    restart: unless-stopped
    depends_on:
      - frontend
      - backend
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
      - ./docker/nginx/certbot/www:/var/www/certbot:ro
      - nginx_logs:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
  
  certbot:
    image: certbot/certbot:latest
    container_name: monografiya-certbot
    volumes:
      - ./docker/nginx/ssl:/etc/letsencrypt
      - ./docker/nginx/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  nginx_logs:
```

## Frontend Dockerfile.dev

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

## docker/postgres/init.sql

```sql
-- Kerakli extension'lar
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

## Asosiy komandalar

### Birinchi marta ishga tushirish

```bash
# .env fayllarni nusxalash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Servislarni ishga tushirish
docker compose up -d --build

# Migrate (avtomatik bo'ladi, lekin qo'lda ham mumkin)
docker compose exec backend alembic upgrade head

# Seed
docker compose exec backend python -m scripts.seed

# Loglarni ko'rish
docker compose logs -f backend
```

### Kunlik foydalanish

```bash
# Boshlash
docker compose up -d

# To'xtatish
docker compose down

# Birgina servisni qayta yuklash
docker compose restart backend

# Container ichiga kirish
docker compose exec backend bash
docker compose exec db psql -U postgres -d monografiya

# Loglar
docker compose logs -f
docker compose logs -f backend frontend
```

### Production deploy

```bash
# Server'da
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Yangi migratsiya
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head

# Kuzatish
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=100
```

### Backup

```bash
# Database backup
docker compose exec db pg_dump -U postgres monografiya | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# MinIO backup
docker run --rm -v monografiya_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data

# Restore
gunzip -c backup_20250115.sql.gz | docker compose exec -T db psql -U postgres -d monografiya
```

### Tozalash

```bash
# Containerlar va volumelar (ATROFLI! Data o'chadi!)
docker compose down -v

# Faqat containerlar
docker compose down

# Image larni ham
docker compose down --rmi all
```

## Resource cheklash (prod uchun)

`docker-compose.prod.yml`'ga qo'shing:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          memory: 512M
  
  db:
    deploy:
      resources:
        limits:
          memory: 2G
```

## Healthcheck

Har servisning sog'lig'ini tekshirish:

```bash
docker compose ps

# Yoki
docker inspect monografiya-backend --format='{{json .State.Health}}'
```

**Keyingi qadam:** `07-deployment/02-nginx-ssl.md`
