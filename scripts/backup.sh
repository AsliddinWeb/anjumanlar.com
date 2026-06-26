#!/usr/bin/env bash
# Daily backup — runs from /opt/monografiya.com via cron.
#
# Dumps:
#   1. PostgreSQL — pg_dump (custom format, gzipped), readable by pg_restore
#   2. MinIO data volume — tar+gz of the docker volume
#
# Output: /var/backups/monografiya/YYYYMMDD-HHMMSS/
# Retention: BACKUP_RETENTION_DAYS (default 30) — older directories are pruned.
#
# Designed to be idempotent + cron-safe (no interactive prompts, safe stderr).
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/monografiya.com}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/monografiya}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPOSE="docker compose -f docker-compose.prod.yml"

# --- sanity ---------------------------------------------------------------
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "Project dir missing: $PROJECT_DIR" >&2
    exit 1
fi
cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
    echo ".env missing in $PROJECT_DIR — run setup first" >&2
    exit 1
fi

# Pull DB creds from .env without leaking the file's other secrets.
DB_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2-)
DB_NAME=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2-)
DB_USER="${DB_USER:-monografiya}"
DB_NAME="${DB_NAME:-monografiya}"

TS=$(date -u +%Y%m%d-%H%M%S)
DEST="$BACKUP_DIR/$TS"
mkdir -p "$DEST"

echo "==> [$TS] backup start → $DEST"

# --- 1. PostgreSQL --------------------------------------------------------
echo "==> dumping postgres ($DB_USER/$DB_NAME)"
$COMPOSE exec -T postgres pg_dump \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-acl \
    | gzip > "$DEST/postgres.dump.gz"

dump_size=$(stat -c%s "$DEST/postgres.dump.gz" 2>/dev/null || stat -f%z "$DEST/postgres.dump.gz")
echo "==> postgres dump: ${dump_size} bytes"

# --- 2. MinIO volume ------------------------------------------------------
# Tarring the named volume directly is the cheapest route — alternative
# would be ``mc mirror`` against MinIO API which is heavier and needs
# credentials in this script.
echo "==> snapshotting minio_data volume"
docker run --rm \
    -v monografiya_minio_data:/data:ro \
    -v "$DEST":/backup \
    alpine:3.20 \
    sh -c "cd /data && tar czf /backup/minio_data.tar.gz ."

minio_size=$(stat -c%s "$DEST/minio_data.tar.gz" 2>/dev/null || stat -f%z "$DEST/minio_data.tar.gz")
echo "==> minio snapshot: ${minio_size} bytes"

# --- 3. retention ---------------------------------------------------------
echo "==> pruning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" \
    -print -exec rm -rf {} +

echo "==> [$TS] backup done"
