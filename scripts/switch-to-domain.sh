#!/usr/bin/env bash
# Switch from IP:port mode to domain mode.
#
# What it does:
#   1. Updates .env URLs from http://SERVER-IP:port to https://DOMAIN.
#   2. Removes docker-compose.override.ip.yml (so nginx + certbot start).
#   3. Rebuilds frontend image — NUXT_PUBLIC_API_BASE is baked into the
#      JS bundle at build time, so the new URL needs a fresh build.
#   4. Brings everything down + up via prod compose alone.
#   5. Prints next steps: obtain cert + swap nginx config.
#
# Usage:
#   scripts/switch-to-domain.sh                 # default monografiya.com
#   scripts/switch-to-domain.sh monografiya.com

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DOMAIN="${1:-monografiya.com}"
EMAIL="${2:-metalapex82@gmail.com}"

if [[ ! -f .env ]]; then
    echo ".env topilmadi — avval scripts/bootstrap-prod.sh ni ishga tushir" >&2
    exit 1
fi

echo "==> Domen: $DOMAIN"
echo "==> Cert email: $EMAIL"
read -rp "Davom etamizmi? (y/N) " confirm
[[ "$confirm" == "y" || "$confirm" == "Y" ]] || { echo "bekor qilindi"; exit 0; }

# --- .env URLs --------------------------------------------------------------
echo "==> .env URL'larini domenga almashtirayapman"
sed -i "s|^NUXT_PUBLIC_API_BASE=.*|NUXT_PUBLIC_API_BASE=https://$DOMAIN/api/v1|" .env
sed -i "s|^NUXT_PUBLIC_SITE_URL=.*|NUXT_PUBLIC_SITE_URL=https://$DOMAIN|" .env
sed -i "s|^FRONTEND_URL=.*|FRONTEND_URL=https://$DOMAIN|" .env
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN|" .env
sed -i "s|^MINIO_PUBLIC_ENDPOINT=.*|MINIO_PUBLIC_ENDPOINT=https://files.$DOMAIN|" .env

# Revert BIND vars back to 127.0.0.1 (nginx fronts everything now)
for var in POSTGRES_BIND REDIS_BIND MINIO_API_BIND MINIO_CONSOLE_BIND \
           MEILISEARCH_BIND BACKEND_BIND FRONTEND_BIND; do
    sed -i "/^$var=/d" .env
done

# --- remove IP override -----------------------------------------------------
if [[ -f docker-compose.override.ip.yml ]]; then
    mv docker-compose.override.ip.yml docker-compose.override.ip.yml.bak
    echo "==> docker-compose.override.ip.yml o'chirildi (.bak sifatida saqlandi)"
fi

COMPOSE="docker compose -f docker-compose.prod.yml"

# --- rebuild frontend (URL is baked into JS bundle at build time) -----------
echo "==> frontend image'ni qayta yig'yapman (URL build paytida bake qilinadi)"
$COMPOSE build frontend

# --- restart all services ---------------------------------------------------
echo "==> servislarni qayta ko'tarayapman"
$COMPOSE down
$COMPOSE up -d

echo "==> backend healthy bo'lishini kutyapman"
for i in $(seq 1 60); do
    if $COMPOSE exec -T backend curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "    backend healthy"
        break
    fi
    sleep 2
done

# --- print next steps -------------------------------------------------------
cat <<EOF

================================================================
  Domenga o'tildi. Sayt hozir $DOMAIN da HTTP orqali ishlayapti.

  Tekshir:
    curl -I http://$DOMAIN          # 200 yoki Nuxt javobi
    curl -I http://www.$DOMAIN      # 200

  Endi quyidagilarni QO'LDA bajar:

  1) Sertifikat olish (3 ta domen uchun bitta SAN cert):

     $COMPOSE run --rm certbot certonly \\
         --webroot --webroot-path=/var/www/certbot \\
         --email $EMAIL --agree-tos --no-eff-email \\
         -d $DOMAIN -d www.$DOMAIN -d files.$DOMAIN

  2) Nginx config'ni HTTPS'ga almashtir:

     mv nginx/conf.d/monografiya.com.conf \\
        nginx/conf.d/_monografiya.com.bootstrap.conf.disabled
     mv nginx/conf.d/monografiya.com.ssl.conf.disabled \\
        nginx/conf.d/monografiya.com.conf
     $COMPOSE exec nginx nginx -t
     $COMPOSE exec nginx nginx -s reload

  3) Tekshir:
     curl -I https://$DOMAIN
     curl https://$DOMAIN/api/v1/ping
================================================================
EOF
