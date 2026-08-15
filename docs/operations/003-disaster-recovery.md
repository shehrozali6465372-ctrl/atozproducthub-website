# 003 — Disaster Recovery (M11 Phase E)

- **Date:** 2026-08-14
- **Owner:** @atoz/platform
- **Artifacts:** `infra/db/backup.sh`, `infra/db/restore.sh`,
  `tools/db/staging-recovery-drill.sh` (full staging drill + RPO/RTO
  evidence), CI `recovery` job (backup → wipe → restore → verify every
  push)

## 1. RPO / RTO

| Data class | RPO target | RTO target | Mechanism |
|---|---|---|---|
| Business operational (Postgres) | 15 minutes | 4 hours | Automated `pg_dump` (custom format) every 15 min + S3-compatible upload; retention 14 days |
| Public content (articles, products) | N/A | 1 hour | CDN + object storage (content bodies); rebuildable from DB metadata |
| Analytics warehouse (ClickHouse) | 24 hours | 8 hours | ClickHouse partition backup; nightly snapshot |
| Pin/affiliate ledgers | 15 minutes | 4 hours | Append-only tables covered by the Postgres dump |
| Search index (Typesense) | 24 hours | 4 hours | Rebuildable from the event stream / content export |

## 2. Backup

- `infra/db/backup.sh` dumps `PGDATABASE` in custom format (compressed,
  restoreable), prunes dumps older than `RETENTION_DAYS` (default 14), and
  uploads to `s3://${S3_BUCKET}/postgres/` when `S3_BUCKET` is set
  (S3-compatible endpoints supported via `S3_ENDPOINT`).
- Credentials come from the environment (`PGPASSWORD`, `AWS_*`) — never
  from files in git.
- Deployment wiring: a `backup` sidecar/systemd timer runs the script on
  the host; the deployment workflow documents the schedule.

## 3. Restore drill (automated, per push)

The CI `recovery` job proves the pipeline end to end on every push:

1. Fresh PostgreSQL 16 service container.
2. Seed `drill_check` table with a row (`recover-me`).
3. `backup.sh` → dump file.
4. Wipe the table.
5. `restore.sh` → `pg_restore --clean --if-exists`.
6. Assert the row and row count are back.

If any step fails, CI is red — restore is a tested property, not a hope.

## 3a. Staging recovery drill (M11 Phase 3, ADR-0014)

`tools/db/staging-recovery-drill.sh` extends the CI drill for staging:

1. Seed representative data (append-only drill tables with an idempotency
   constraint).
2. Backup via `infra/db/backup.sh`.
3. Destroy the drill tables (simulated data loss).
4. Restore via `infra/db/restore.sh`.
5. Verify rows and that the idempotency constraint survived restore.
6. Re-run migrations when `RUN_MIGRATIONS=1` (forward migration on
   restored data).
7. Verify application readiness when `STAGING_BASE_URL` is set.
8. Write `staging-recovery-report.md` with restore duration and RPO/RTO
   evidence.

Live staging RTO actuals are a Phase H gate recorded against the 4-hour
target; CI proves the restore path on every push, the staging host records
real durations.

## 4. DR runbook

### Scenario A — Postgres data loss / corruption
1. Stop write traffic (scale down automation/analytics ingestion).
2. `BACKUP_FILE=<latest or chosen dump> bash infra/db/restore.sh`
   (optionally download from `s3://${S3_BUCKET}/postgres/` first).
3. Run migrations `alembic upgrade head` if the backup predates a
   migration (forward-migrate after restore).
4. Verify `/ready` on every service, then reopen traffic.
5. Record RTO actual vs target in the incident log.

### Scenario B — Redis total loss
1. Redis holds only the live working set; the durable source is
   `queue_items`/`job_runs` in Postgres (ADR-0010).
2. Restart Redis (`--appendonly yes` replays the AOF); automation
   re-claims due work from the ledger on the next Beat tick.

### Scenario C — Kafka loss
1. Recreate the topic (`atoz.analytics.events.v1`); producers rebuffer.
2. ClickHouse rollups reconcile from Postgres ledgers (M8 design).

### Scenario D — Region/availability-zone loss
1. Provision the stack from IaC in the secondary region (Phase F).
2. Restore the latest Postgres dump, point DNS to the secondary origin.
3. RTO tracked against the 4 h target; quarterly full-dress drill.

## 5. Migration recovery

- CI validates downgrade + re-upgrade for every migration stream on fresh
  PostgreSQL (database job), so schema changes are reversible.
- After a failed deploy, the rollback procedure (004) restores the previous
  image; the DB is forward-compatible because migrations are additive and
  rollback-safe by policy (no destructive changes without a release window).
