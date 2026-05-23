#!/usr/bin/env bash
# Restore a backup directory created by scripts/backup.sh.
#
# Usage:
#   ./scripts/restore.sh /var/backups/anjumanlar/20260801-030000
#
# Restores both the postgres dump and the minio data tarball. The script
# will refuse to run if the target database already contains rows you
# didn't explicitly opt into clobbering — pass --force to override.
#
# WHAT THIS WIPES:
#   - Every row in every table inside the configured POSTGRES_DB
#   - Every object in the docker volume ``anjumanlar_minio_data``
#
# Use the dry-run flag (``--dry-run``) to see what would happen first.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/anjumanlar.com}"
COMPOSE="docker compose -f docker-compose.prod.yml"

FORCE=0
DRY_RUN=0
BACKUP=""

usage() {
    cat <<EOF >&2
Usage: $0 [--force] [--dry-run] <backup-dir>
EOF
    exit 1
}

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        --dry-run) DRY_RUN=1 ;;
        -h|--help) usage ;;
        *) BACKUP="$arg" ;;
    esac
done

if [[ -z "$BACKUP" ]]; then
    usage
fi
if [[ ! -d "$BACKUP" ]]; then
    echo "Backup dir not found: $BACKUP" >&2
    exit 1
fi
if [[ ! -f "$BACKUP/postgres.dump.gz" || ! -f "$BACKUP/minio_data.tar.gz" ]]; then
    echo "Backup dir is missing expected files (postgres.dump.gz, minio_data.tar.gz)" >&2
    exit 1
fi

cd "$PROJECT_DIR"
DB_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2-)
DB_NAME=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2-)
DB_USER="${DB_USER:-anjumanlar}"
DB_NAME="${DB_NAME:-anjumanlar}"

# --- refuse to overwrite a populated DB unless --force --------------------
if [[ "$FORCE" -ne 1 ]]; then
    has_data=$($COMPOSE exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT EXISTS(SELECT 1 FROM users LIMIT 1)" 2>/dev/null || echo "f")
    if [[ "$has_data" == "t" ]]; then
        echo "users table is non-empty. Re-run with --force to clobber." >&2
        exit 1
    fi
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would restore postgres from $BACKUP/postgres.dump.gz"
    echo "[dry-run] would restore minio from $BACKUP/minio_data.tar.gz"
    exit 0
fi

# --- 1. postgres ----------------------------------------------------------
echo "==> dropping + recreating database $DB_NAME"
$COMPOSE exec -T postgres psql -U "$DB_USER" -d postgres -c \
    "DROP DATABASE IF EXISTS \"$DB_NAME\";"
$COMPOSE exec -T postgres psql -U "$DB_USER" -d postgres -c \
    "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"

echo "==> restoring postgres dump"
gunzip -c "$BACKUP/postgres.dump.gz" \
    | $COMPOSE exec -T postgres pg_restore \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --no-owner \
        --no-acl

# --- 2. minio data --------------------------------------------------------
echo "==> stopping minio + wiping volume contents"
$COMPOSE stop minio
docker run --rm \
    -v anjumanlar_minio_data:/data \
    alpine:3.20 \
    sh -c "rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null || true"

echo "==> restoring minio data tarball"
docker run --rm \
    -v anjumanlar_minio_data:/data \
    -v "$BACKUP":/backup:ro \
    alpine:3.20 \
    sh -c "cd /data && tar xzf /backup/minio_data.tar.gz"

$COMPOSE start minio

echo "==> restore done. Re-run migrations + restart workers just in case:"
echo "    $COMPOSE exec backend alembic upgrade head"
echo "    $COMPOSE restart backend celery_worker celery_beat"
