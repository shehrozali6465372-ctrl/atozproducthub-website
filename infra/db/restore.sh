#!/usr/bin/env bash
# PostgreSQL restore (M11 Phase E — restore drill and DR).
#
# Restores the latest local custom-format dump (or BACKUP_FILE when set)
# into PGDATABASE with --clean --if-exists, so a restore drill can wipe and
# rebuild the target database. Credentials come from the environment only.
set -euo pipefail

: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGUSER:=atoz}"
: "${PGDATABASE:=atoz}"
: "${BACKUP_DIR:=./backups}"
: "${BACKUP_FILE:=}"

if [ -z "$BACKUP_FILE" ]; then
  BACKUP_FILE="$(ls -1t "${BACKUP_DIR}"/${PGDATABASE}-*.dump 2>/dev/null | head -1 || true)"
fi
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "restore: no backup file found under ${BACKUP_DIR}" >&2
  exit 1
fi

echo "restore: restoring ${BACKUP_FILE} -> ${PGDATABASE}@${PGHOST}:${PGPORT}"
pg_restore -Fc -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  --clean --if-exists "$BACKUP_FILE"
echo "restore: complete"
