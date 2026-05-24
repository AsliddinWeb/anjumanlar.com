#!/usr/bin/env bash
# Production deploy script — run on the server from /opt/monografiya.com.
#
# What it does:
#   1. git pull (fast-forward only)
#   2. docker compose build
#   3. docker compose up -d
#   4. alembic upgrade head
#   5. seed categories (idempotent)
#   6. nginx reload (in-container)
#
# First-time? See DEPLOY.md for the bootstrap (clone, .env, certbot).
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
COMPOSE_FILE="docker-compose.prod.yml"

# --- sanity checks ---------------------------------------------------------
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Not at the project root — expected $COMPOSE_FILE here" >&2
    exit 1
fi
if [[ ! -f .env ]]; then
    echo ".env missing — copy .env.prod.example to .env and fill secrets first" >&2
    exit 1
fi

echo "==> pulling latest main"
git fetch --quiet
git pull --ff-only

echo "==> building images"
$COMPOSE build

echo "==> bringing services up"
$COMPOSE up -d

echo "==> waiting for backend to become healthy"
for i in $(seq 1 30); do
    status=$($COMPOSE ps backend --format json 2>/dev/null \
        | python3 -c "import json,sys; rows=[json.loads(l) for l in sys.stdin if l.strip()]; print(rows[0].get('Health','starting') if rows else 'missing')" \
        || echo "starting")
    if [[ "$status" == "healthy" ]]; then
        break
    fi
    sleep 2
done

echo "==> running alembic migrations"
$COMPOSE exec -T backend alembic upgrade head

echo "==> seeding categories"
$COMPOSE exec -T backend python -m app.scripts.seed_categories

echo "==> reloading nginx config"
$COMPOSE exec nginx nginx -s reload || true

echo "==> done"
$COMPOSE ps
