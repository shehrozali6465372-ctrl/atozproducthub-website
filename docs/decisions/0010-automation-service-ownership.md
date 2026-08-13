# ADR-0010 — Automation Service Database Ownership and Idempotency Extension

- **Status:** Accepted
- **Date:** 2026-08-13
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 03-module-boundaries.md, 11-database-architecture.md (annotations), 14-implementation-roadmap.md, CHANGELOG.md

## Context

Task 20 (M10, Phase 12 Step 1) implements the durable automation engine
foundation: `automation_rules` / `automation_runs` (Database Blueprint
§5.21), `scheduled_jobs` / `job_runs` (§5.22), `queue_items` (§5.23), and
`aios_job_records` (§5.29). The Database Blueprint assigns
`scheduled_jobs`, `job_runs`, and `queue_items` to the **Platform** module,
and ADR-0009 (M9) already created those physical tables inside the
admin-service migration stream on the shared PostgreSQL database.

Two conflicts must be resolved before implementing:

1. **Duplicate table ownership:** if the automation-service migration
   stream also created `scheduled_jobs` / `job_runs` / `queue_items`, the
   CI migration job (which runs every service stream sequentially against
   the same physical `atoz` database) would fail with duplicate-table
   errors. The M10 spec (Task 20) lists these tables as part of the
   automation domain while the frozen blueprint assigns them to Platform.
2. **Idempotent rule triggers:** the M10 spec requires idempotency keys
   and duplicate prevention for automation runs; Database Blueprint §5.21
   does not define an idempotency column for `automation_runs`.

## Decision

1. **Service-owned tables (automation-service migration stream,
   `alembic_version_automation`):** `automation_niches` (local tenancy
   mirror, same policy as `admin_niches` / `analytics_niches`),
   `automation_rules`, `automation_runs`, and `aios_job_records`.
2. **Platform tables remain admin-owned:** `scheduled_jobs`, `job_runs`,
   and `queue_items` are **not** created by the automation migration
   stream. The automation service maps ORM entities onto those exact
   physical tables (identical names/columns/constraints as ADR-0009) and
   integrates through the same rows — reads, enqueue, execution records,
   and queue-ledger transitions. Admin-service remains the migration owner;
   automation-service is a co-writer for its execution lifecycle.
3. **Idempotency extension:** `automation_runs` gains a nullable
   `idempotency_key` column with a unique index (ADR-0010 annotation to
   §5.21). A client-supplied `Idempotency-Key` on rule trigger is globally
   unique; a replay returns the existing run instead of duplicating
   execution history. The same column is used by `aios_job_records`
   (`UNIQUE (job_id, contract)`) per the existing §5.29 shape.
4. **Tenancy:** every scoped automation record carries `niche_id`
   (nullable for global rules/jobs, mandatory for `aios_job_records`).
   The `X-Niche-Id` header selects the scope; absent header = global
   compartment only; present header = strict niche compartment. Scope
   mismatches resolve as not-found (no cross-niche leakage).
5. **Celery:** the application/worker/Beat scaffold
   (`celery_app.py` / `celery_worker.py`) is wired from environment
   (`CELERY_BROKER_URL`, `CELERY_BACKEND_URL`) with no business tasks in
   the foundation (Step 2 registers executors against the queue ledger).

## Consequences

- The automation stream coexists with all sibling streams on the same
  physical PostgreSQL database; CI validates it on a fresh database.
- No competing migration creates Platform tables; M9 admin-service keeps
  full ownership and its migration tests stay green.
- Rule/queue/job state machines, retry/backoff, idempotency, tenancy, and
  Bridge correlation are testable foundation primitives for Step 2
  (Pinterest publishing, sitemap rebuild, affiliate reconciliation, AI OS
  job dispatch).
- `aios_job_records` continues to store correlation metadata only —
  never prompts, generated-content internals, or learning data (§5.29
  boundary statement).

## Contract compliance

- No AI functionality: the service hosts business workflow execution only;
  nothing here generates, learns, researches, or routes intelligence.
- Business layer only; AI OS contact remains exclusively via the Bridge;
  `aios_job_records` is the website-side correlation ledger.
- Tenancy and no-duplicate-features policies hold; Platform queue/job
  tables keep a single migration owner.
