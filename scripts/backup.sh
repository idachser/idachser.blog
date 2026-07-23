#!/usr/bin/env bash
#
# Backup the production database and uploaded media.
#
#   - Postgres  -> pg_dump custom format (.dump, already compressed)
#   - uploads   -> tar.gz of /app/uploads from the running web container
#
# Runs on the host from cron, out of the deployed git checkout
# ($PROD_APP_DIR/scripts/backup.sh). Backups are written to
# $PROD_APP_DIR/backups (outside any docker volume); only the newest
# KEEP of each kind are kept. The local machine pulls them via rsync.

set -euo pipefail

# --- paths (derived from this script's location: repo/scripts/backup.sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"

# --- config ------------------------------------------------------------
DB_SERVICE="db"
WEB_SERVICE="web"
BACKUP_DIR="${PROJECT_DIR}/backups"
KEEP=5   # newest backups of each kind to retain
# -----------------------------------------------------------------------

# Read a single KEY=value from .env (ignores comments, strips quotes).
get_env() {
  sed -n "s/^${1}=//p" "$ENV_FILE" | tail -n1 | tr -d '"'"'"
}

DB_USER="$(get_env POSTGRES_USER)"
DB_NAME="$(get_env POSTGRES_DB)"
: "${DB_USER:?POSTGRES_USER not found in ${ENV_FILE}}"
: "${DB_NAME:?POSTGRES_DB not found in ${ENV_FILE}}"

TS="$(date +%Y%m%d-%H%M%S)"
DB_FILE="${BACKUP_DIR}/db-${TS}.dump"
MEDIA_FILE="${BACKUP_DIR}/uploads-${TS}.tar.gz"

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

mkdir -p "$BACKUP_DIR"

echo "[backup] dumping database ${DB_NAME} -> ${DB_FILE}"
compose exec -T "$DB_SERVICE" \
  pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "${DB_FILE}.part"
mv "${DB_FILE}.part" "$DB_FILE"

echo "[backup] archiving uploads -> ${MEDIA_FILE}"
compose exec -T "$WEB_SERVICE" \
  tar czf - -C /app uploads > "${MEDIA_FILE}.part"
mv "${MEDIA_FILE}.part" "$MEDIA_FILE"

# Keep only the newest $KEEP files matching a glob, delete the rest.
prune() {
  local pattern="$1"
  ls -1t ${pattern} 2>/dev/null | tail -n "+$((KEEP + 1))" | while IFS= read -r f; do
    echo "[backup] pruning old backup: $f"
    rm -f -- "$f"
  done
}

echo "[backup] keeping newest ${KEEP} backups of each kind"
prune "${BACKUP_DIR}/db-*.dump"
prune "${BACKUP_DIR}/uploads-*.tar.gz"

echo "[backup] done: $(du -h "$DB_FILE" "$MEDIA_FILE" | awk '{print $1, $2}')"
