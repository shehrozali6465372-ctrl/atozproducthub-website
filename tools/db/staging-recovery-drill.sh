#!/usr/bin/env bash
# Staging recovery drill (Task 24 / M11 Phase 3, ADR-0014).
#
# Full backup → destroy → restore cycle with evidence:
#   1. Seed representative staging data (append-only drill tables with an
#      idempotency constraint).
#   2. Create a PostgreSQL backup (infra/db/backup.sh).
#   3. Destroy the drill tables (simulated data loss).
#   4. Restore the backup (infra/db/restore.sh).
#   5. Verify rows and the idempotency constraint survived.
#   6. Re-run migrations when RUN_MIGRATIONS=1 (validates forward
#      migration on restored data).
#   7. Verify application readiness when STAGING_BASE_URL is set.
#   8. Record restore duration and RPO/RTO evidence in the report file.
#
# Never touches production data: only PGDATABASE is used, and only the
# drill_* tables are destroyed/recreated by this script.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGUSER:=atoz}"
: "${PGDATABASE:=atoz}"
: "${PGPASSWORD:=}"
: "${BACKUP_DIR:=./backups}"
: "${REPORT_FILE:=staging-recovery-report.md}"
: "${RUN_MIGRATIONS:=0}"
: "${STAGING_BASE_URL:=}"

export PGHOST PGPORT PGUSER PGDATABASE PGPASSWORD BACKUP_DIR

if [ -z "$PGPASSWORD" ]; then
  echo "PGPASSWORD required" >&2
  exit 1
fi

PSQL=(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1)

START="$(date -u +%s)"
START_ISO="$(date -u -Iseconds)"

echo "== staging recovery drill: seed =="
"${PSQL[@]}" <<'SQL'
CREATE TABLE IF NOT EXISTS drill_check (id integer PRIMARY KEY, payload text NOT NULL);
CREATE TABLE IF NOT EXISTS drill_ledger (
  id integer PRIMARY KEY,
  idempotency_key text NOT NULL,
  payload text NOT NULL,
  UNIQUE (idempotency_key)
);
TRUNCATE drill_check, drill_ledger;
INSERT INTO drill_check VALUES (1, 'recover-me'), (2, 'niche-a');
INSERT INTO drill_ledger VALUES (10, 'evt-0001', 'click'), (11, 'evt-0002', 'conversion');
SQL

echo "== staging recovery drill: backup =="
bash infra/db/backup.sh

echo "== staging recovery drill: destroy =="
"${PSQL[@]}" -c "DROP TABLE drill_check, drill_ledger;"

echo "== staging recovery drill: restore =="
bash infra/db/restore.sh

echo "== staging recovery drill: verify data =="
CHECK_PAYLOAD="$("${PSQL[@]}" -tAc "SELECT payload FROM drill_check WHERE id = 1")"
LEDGER_COUNT="$("${PSQL[@]}" -tAc "SELECT count(*) FROM drill_ledger")"
[ "$CHECK_PAYLOAD" = "recover-me" ] || { echo "FAIL: drill_check row missing after restore"; exit 1; }
[ "$LEDGER_COUNT" = "2" ] || { echo "FAIL: drill_ledger row count ${LEDGER_COUNT}, expected 2"; exit 1; }
echo "OK: restored rows verified (drill_check=recover-me, drill_ledger=2)"

echo "== staging recovery drill: idempotency constraint =="
if "${PSQL[@]}" -c "INSERT INTO drill_ledger VALUES (12, 'evt-0001', 'duplicate')" >/dev/null 2>&1; then
  echo "FAIL: duplicate idempotency_key insert succeeded after restore"
  exit 1
fi
echo "OK: idempotency constraint survived restore"

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "== staging recovery drill: migrations after restore =="
  bash tools/db/validate-migrations.sh upgrade
  echo "OK: migrations re-run successfully on restored data"
fi

if [ -n "$STAGING_BASE_URL" ]; then
  echo "== staging recovery drill: application readiness =="
  for _ in $(seq 1 30); do
    if curl -fsS "${STAGING_BASE_URL}/ready" >/dev/null 2>&1; then
      echo "OK: ${STAGING_BASE_URL}/ready healthy after restore"
      break
    fi
    sleep 2
  done
  if ! curl -fsS "${STAGING_BASE_URL}/ready" >/dev/null 2>&1; then
    echo "FAIL: application did not become ready after restore"
    exit 1
  fi
fi

END="$(date -u +%s)"
DURATION="$((END - START))"
END_ISO="$(date -u -Iseconds)"

cat > "$REPORT_FILE" <<EOF
# Staging recovery drill evidence

- Started: ${START_ISO}
- Completed: ${END_ISO}
- Restore duration: ${DURATION}s
- Database: ${PGDATABASE}@${PGHOST}:${PGPORT}
- Backup dir: ${BACKUP_DIR}
- Migrations after restore: $([ "$RUN_MIGRATIONS" = "1" ] && echo yes || echo no)
- Application readiness verified: $([ -n "$STAGING_BASE_URL" ] && echo yes || echo no)
- RPO evidence: backup taken immediately before destroy; restored data equals
  the seeded snapshot (no post-backup writes existed).
- RTO evidence: restore completed in ${DURATION}s on this host (target 4 h).

Next: attach this file to the staging validation report
(docs/operations/007-staging-validation.md) as Phase H evidence.
EOF

echo "== staging recovery drill: OK (${DURATION}s) =="
