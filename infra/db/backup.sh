#!/usr/bin/env bash
# PostgreSQL automated backup (M11 Phase E).
#
# Produces a custom-format pg_dump (compressed, restoreable) into BACKUP_DIR
# with retention cleanup, and optionally uploads it to S3-compatible object
# storage when S3_BUCKET is set. Credentials come from the environment
# (PGPASSWORD / AWS_*), never from arguments or files in git.
set -euo pipefail

: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGUSER:=atoz}"
: "${PGDATABASE:=atoz}"
: "${BACKUP_DIR:=./backups}"
: "${RETENTION_DAYS:=14}"
: "${S3_BUCKET:=}"
: "${S3_ENDPOINT:=}"

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="${BACKUP_DIR}/${PGDATABASE}-${TIMESTAMP}.dump"

echo "backup: dumping ${PGDATABASE}@${PGHOST}:${PGPORT} -> ${FILE}"
pg_dump -Fc -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$FILE"

echo "backup: pruning dumps older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name "${PGDATABASE}-*.dump" -mtime +"${RETENTION_DAYS}" -delete

if [ -n "$S3_BUCKET" ]; then
  echo "backup: uploading to s3://${S3_BUCKET}/postgres/"
  aws s3 cp "$FILE" "s3://${S3_BUCKET}/postgres/" ${S3_ENDPOINT:+--endpoint-url "$S3_ENDPOINT"}
fi

echo "backup: complete"
