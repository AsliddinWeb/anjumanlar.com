#!/usr/bin/env bash
# Production deploy script — run on the server from /opt/monografiya.com.
#
# What it does:
#   1. git pull (fast-forward only)
#   2. diff against the SHA of the last *successfully completed* deploy
#      (tracked in .deploy-state, not just "whatever git pull last saw") and
#      build only the image(s) that need it — Vite's production build has
#      no incremental cache, so a frontend rebuild always costs ~3-4 min,
#      not worth paying for a backend-only fix
#   3. docker compose up -d (only the affected services)
#   4. alembic upgrade head
#   5. seed categories (idempotent)
#   6. nginx reload (in-container)
#   7. record this SHA in .deploy-state — only on a clean, uninterrupted run
#
# .deploy-state (not the git SHA `git pull` leaves you on) is the source of
# truth for "what's actually running": if a previous run was Ctrl-C'd or
# failed partway through, it never got updated, so the next run correctly
# re-diffs from the last point that really made it all the way to `up -d`,
# instead of silently assuming an interrupted build counted.
#
# Usage:
#   ./scripts/deploy.sh            # auto-detect from what changed since .deploy-state
#   ./scripts/deploy.sh backend    # force a backend-only deploy
#   ./scripts/deploy.sh frontend   # force a frontend-only deploy
#   ./scripts/deploy.sh all        # force a full rebuild of both
#
# First-time? See DEPLOY.md for the bootstrap (clone, .env, certbot).
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
COMPOSE_FILE="docker-compose.prod.yml"
STATE_FILE=".deploy-state"
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
    git pull --ff-only
    # This file may have just been rewritten by the pull above. A running
    # bash process reads its script from disk as it goes, so continuing
    # in-place risks executing a mix of old and new logic. `exec` replaces
    # the process image outright, forcing a clean re-read of whatever is
    # on disk now — cheap (bash startup only) and removes the hazard.
    echo "==> re-executing (picks this file up fresh in case it just changed)"
    exec env DEPLOY_SH_REEXEC=1 bash "$0" "$FORCE"
fi

AFTER_SHA=$(git rev-parse HEAD)
LAST_DEPLOYED_SHA=""
[[ -f "$STATE_FILE" ]] && LAST_DEPLOYED_SHA=$(cat "$STATE_FILE")

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
elif [[ -z "$LAST_DEPLOYED_SHA" ]]; then
    echo "==> no record of a prior successful deploy ($STATE_FILE missing) — building both"
    BUILD_BACKEND=1
    BUILD_FRONTEND=1
elif [[ "$LAST_DEPLOYED_SHA" == "$AFTER_SHA" ]]; then
    echo "==> already fully deployed at $AFTER_SHA — skipping build (pass 'all' to force one anyway)"
else
    CHANGED=$(git diff --name-only "$LAST_DEPLOYED_SHA" "$AFTER_SHA" 2>/dev/null || true)
    if [[ -z "$CHANGED" ]]; then
        echo "==> can't diff from the recorded last deploy ($LAST_DEPLOYED_SHA) — building both to be safe"
        BUILD_BACKEND=1
        BUILD_FRONTEND=1
    else
        echo "==> files changed since the last successful deploy ($LAST_DEPLOYED_SHA):"
        echo "$CHANGED" | sed 's/^/     /'
        if echo "$CHANGED" | grep -qE '^backend/|^docker-compose\.prod\.yml$'; then
            BUILD_BACKEND=1
        fi
        if echo "$CHANGED" | grep -qE '^frontend/|^docker-compose\.prod\.yml$'; then
            BUILD_FRONTEND=1
        fi
        if [[ "$BUILD_BACKEND" -eq 0 && "$BUILD_FRONTEND" -eq 0 ]]; then
            echo "==> changed files are outside backend/ and frontend/ — nothing to build"
        fi
    fi
fi

if [[ "$BUILD_BACKEND" -eq 0 && "$BUILD_FRONTEND" -eq 0 ]]; then
    echo "$AFTER_SHA" > "$STATE_FILE"
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

# Only reached if every step above succeeded (`set -e` aborts otherwise) —
# safe to record this as the last known-good deploy.
echo "$AFTER_SHA" > "$STATE_FILE"

echo "==> done"
$COMPOSE ps
