#!/usr/bin/env bash
# Install the daily backup job into root's crontab.
#
# Idempotent — re-running just refreshes the entry. The cron line:
#   - runs backup.sh at 03:30 UTC (08:30 Tashkent) every day,
#   - sources /etc/environment so PROJECT_DIR / BACKUP_DIR overrides work,
#   - appends stdout + stderr to /var/log/monografiya-backup.log so cron
#     emails don't pile up while still keeping a tail-able audit trail.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/monografiya.com}"
SCRIPT_PATH="$PROJECT_DIR/scripts/backup.sh"
LOG_PATH="/var/log/monografiya-backup.log"
CRON_TAG="# monografiya-backup"

if [[ ! -x "$SCRIPT_PATH" ]]; then
    chmod +x "$SCRIPT_PATH"
fi

# Snapshot the existing crontab, strip our tagged entries, append the fresh one.
tmp=$(mktemp)
crontab -l 2>/dev/null | grep -v -F "$CRON_TAG" > "$tmp" || true
{
    echo "30 3 * * * cd $PROJECT_DIR && bash $SCRIPT_PATH >> $LOG_PATH 2>&1 $CRON_TAG"
} >> "$tmp"
crontab "$tmp"
rm -f "$tmp"

mkdir -p "$(dirname "$LOG_PATH")"
touch "$LOG_PATH"

echo "Installed daily backup at 03:30 UTC."
echo "Logs:  $LOG_PATH"
echo "Run now: bash $SCRIPT_PATH"
