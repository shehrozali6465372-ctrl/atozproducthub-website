# automation-service

Durable business automation engine foundation (M10, v0.10.0): rule/run state
machines, scheduler + queue ledgers, retry policy, and AI OS Bridge
correlation records. Business workflows only — no AI.

- **Owner:** @atoz/platform
- **Status:** M10 foundation — durable engine primitives; Step 2 wires the
  business executors (Pinterest publishing, sitemap rebuild, affiliate
  reconciliation, AI OS job dispatch).
- **Endpoints:**
  - `/health`, `/ready`, `/metrics` (shared backend-core factory)
  - `/api/v1/admin/rules[/{id}/enable|disable|trigger]` — rule lifecycle +
    idempotent triggers (`Idempotency-Key` header)
  - `/api/v1/admin/runs[/{id}/complete|fail]` — append-only run history
  - `/api/v1/admin/scheduled-jobs[/{id}/enable|disable|enqueue]` — Platform
    `scheduled_jobs` + `job_runs` execution records
  - `/api/v1/admin/job-runs[/{id}/start|complete|fail|cancel]` — job execution
    state machine (`pending → running → success/failed/cancelled`)
  - `/api/v1/admin/queue[/enqueue][/{id}/claim|complete|fail]` — durable
    `queue_items` ledger with exponential-backoff retries
  - `/api/v1/admin/aios-jobs[/status]` — Bridge correlation records
    (`UNIQUE (job_id, contract)` dedupe; correlation metadata only)
- **DB migrations:** `db/migrations/` — `automation_db` stream
  (`alembic_version_automation`). **Ownership (ADR-0010):** creates
  `automation_niches`, `automation_rules`, `automation_runs`,
  `aios_job_records` only. The Platform tables `scheduled_jobs`,
  `job_runs`, `queue_items` are created by the admin-service stream
  (ADR-0009) and are integrated here by identical table mapping — never
  re-created.
- **Celery:** `celery_app.py` / `celery_worker.py` scaffold
  (`CELERY_BROKER_URL` / `CELERY_BACKEND_URL`, `acks_late=True`,
  `worker_prefetch_multiplier=1`, empty `beat_schedule`). No business tasks
  in the foundation.
- **Tenancy:** every scoped record carries `niche_id`; the `X-Niche-Id`
  header selects strict niche scope, absence selects the global
  compartment; scope mismatches never resolve (no cross-niche leakage).
  API is JWT RBAC (`automation:read` / `automation:write`).
- **AI OS boundary:** `aios_job_records` stores correlation metadata only —
  no prompts, no generated-content internals, no learning data (§5.29).
  This service never contacts the AI OS directly; all AI OS communication
  flows through `services/aios-bridge/` and `libs/contracts/aios/`.
