#!/usr/bin/env bash
# Production deploy script — run on the server from /opt/monografiya.com.
#
# What it does:
#   1. git pull (fast-forward only)
#   2. figure out what actually changed since the last deploy, and build
#      only the image(s) that need it (Vite's production build has no
#      incremental cache, so a frontend rebuild always costs ~3-4 min —
#      not worth paying for a backend-only fix)
#   3. docker compose up -d (only the affected services)
#   4. alembic upgrade head
#   5. seed categories (idempotent)
#   6. nginx reload (in-container)
#
# Usage:
#   ./scripts/deploy.sh            # auto-detect from the files the pull touched
#   ./scripts/deploy.sh backend    # force a backend-only deploy
#   ./scripts/deploy.sh frontend   # force a frontend-only deploy
#   ./scripts/deploy.sh all        # force a full rebuild of both
#
# First-time? See DEPLOY.md for the bootstrap (clone, .env, certbot).
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
COMPOSE_FILE="docker-compose.prod.yml"
FORCE="${1:-}"

# --- sanity checks ---------------------------------------------------------
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Not at the project root — expected $COMPOSE_FILE here" >&2
    exit 1
fi
if [[ ! -f .env ]]; then
    echo ".env missing — copy .env.prod.example to .env and fill secrets first" >&2
    exit 1
fi
if [[ -n "$FORCE" && "$FORCE" != "backend" && "$FORCE" != "frontend" && "$FORCE" != "all" ]]; then
    echo "Unknown argument: $FORCE (expected: backend, frontend, all, or nothing)" >&2
    exit 1
fi

if [[ -z "${DEPLOY_SH_REEXEC:-}" ]]; then
    echo "==> pulling latest main"
    git fetch --quiet
    BEFORE_SHA=$(git rev-parse HEAD)
    git pull --ff-only
    AFTER_SHA=$(git rev-parse HEAD)

    if [[ "$BEFORE_SHA" != "$AFTER_SHA" ]]; then
        # The pull may have rewritten this very file. A long-running bash
        # process reads its script from disk as it goes, so continuing
        # in-place after a `git pull` that touched scripts/deploy.sh risks
        # running a mix of old and new logic. `exec` replaces the process
        # image outright, forcing a clean re-read of whatever is on disk
        # now — cheap (bash startup only) and eliminates the hazard.
        echo "==> re-executing the freshly pulled script"
        DEPLOY_SH_REEXEC=1 DEPLOY_SH_BEFORE_SHA="$BEFORE_SHA" exec bash "$0" "$FORCE"
    fi
    BEFORE_SHA_FOR_DIFF="$BEFORE_SHA"
else
    BEFORE_SHA_FOR_DIFF="$DEPLOY_SH_BEFORE_SHA"
fi
AFTER_SHA=$(git rev-parse HEAD)
BEFORE_SHA="$BEFORE_SHA_FOR_DIFF"

# --- decide what needs rebuilding -------------------------------------------
BUILD_BACKEND=0
BUILD_FRONTEND=0

if [[ "$FORCE" == "backend" ]]; then
    BUILD_BACKEND=1
elif [[ "$FORCE" == "frontend" ]]; then
    BUILD_FRONTEND=1
elif [[ "$FORCE" == "all" ]]; then
    BUILD_BACKEND=1
    BUILD_FRONTEND=1
elif [[ "$BEFORE_SHA" == "$AFTER_SHA" ]]; then
    echo "==> nothing new on main — skipping build (pass 'all' to force a rebuild anyway)"
else
    CHANGED=$(git diff --name-only "$BEFORE_SHA" "$AFTER_SHA")
    echo "==> files changed since last deploy:"
    echo "$CHANGED" | sed 's/^/     /'
    if echo "$CHANGED" | grep -qE '^backend/|^docker-compose\.prod\.yml$'; then
        BUILD_BACKEND=1
    fi
    if echo "$CHANGED" | grep -qE '^frontend/|^docker-compose\.prod\.yml$'; then
        BUILD_FRONTEND=1
    fi
    # Anything outside backend/ and frontend/ (nginx config, scripts, docs
    # that might still matter, ...) — rebuild both rather than guess wrong.
    if ! echo "$CHANGED" | grep -qE '^backend/|^frontend/|^docker-compose\.prod\.yml$'; then
        echo "==> changed files are outside backend/ and frontend/ — nothing to build"
    fi
fi

if [[ "$BUILD_BACKEND" -eq 0 && "$BUILD_FRONTEND" -eq 0 ]]; then
    echo "==> done (no rebuild needed)"
    $COMPOSE ps
    exit 0
fi

SERVICES=()
[[ "$BUILD_BACKEND" -eq 1 ]] && SERVICES+=(backend celery_worker celery_beat)
[[ "$BUILD_FRONTEND" -eq 1 ]] && SERVICES+=(frontend)

echo "==> building: ${SERVICES[*]}"
# backend/celery_worker/celery_beat share one image — build it once.
if [[ "$BUILD_BACKEND" -eq 1 && "$BUILD_FRONTEND" -eq 1 ]]; then
    $COMPOSE build backend frontend
elif [[ "$BUILD_BACKEND" -eq 1 ]]; then
    $COMPOSE build backend
else
    $COMPOSE build frontend
fi

echo "==> bringing services up: ${SERVICES[*]}"
$COMPOSE up -d "${SERVICES[@]}"

if [[ "$BUILD_BACKEND" -eq 1 ]]; then
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
fi

echo "==> reloading nginx config"
$COMPOSE exec nginx nginx -s reload || true

echo "==> done"
$COMPOSE ps
