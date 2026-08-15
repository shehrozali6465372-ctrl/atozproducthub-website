# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.14.0] - 2026-08-15

### Added

- Implemented Task 24 / M11 Phase 3 — staging deployment & production
  validation (ADR-0014). Feature development is complete; the remaining
  production gates (30-day reliability validation, final Go/No-Go) are
  tracked in `docs/operations/006-launch-audit.md` and require real
  production infrastructure.
- **Phase A — Staging environment:**
  - `infra/docker/compose.staging.yml` — production-like staging overlay
    (project identity `atozproducthub-staging`, `APP_ENV=staging`, staging
    domains/CORS, placeholder AI OS endpoint). Reuses the production
    hardening boundaries; no host ports, no credentials, no `name:`
    override collisions.
  - `config/staging/env.template` + `config/staging/README.md` — staging
    configuration contract; every credential stays an injected variable.
  - `tools/dev/check-staging.sh` — staging guard (service coverage,
    overlay identity, no host ports, no credentials, template variables).
- **Phase B — Deployment pipeline (`.github/workflows/deploy.yml`):**
  - Manual-dispatch pipeline: `validate → build-push → deploy`; images
    tagged with immutable commit SHA and pushed to GHCR.
  - Migration gate runs against the release images *before* rollout;
    fail-closed smoke after rollout; optional staging rollback drill;
    automatic rollback to the previous tag on failure.
  - Production deploys remain approval-gated (environment protection);
    no auto-deploy to production.
  - `tools/deploy/write-image-override.sh`, `run-migration-gate.sh`,
    `staging-smoke.sh`, `rollback-test.sh`.
- **Phase C — Database validation:**
  - `tools/db/validate-migrations.sh` — single head per service stream,
    version-table uniqueness, fresh-DB upgrade, schema smoke, tenancy
    (`niche_id`) checks, unique/idempotency constraints,
    downgrade/re-upgrade; wired into the CI `database` job.
  - `tools/db/staging-recovery-drill.sh` — seed → backup → destroy →
    restore → verify (RPO/RTO evidence, staging data only).
- **Phase D — Staging smoke suite (`tests/staging/`):**
  - `test_staging_smoke.py` — 24-item Phase D matrix (health/readiness,
    auth/RBAC/MFA gates, `X-Niche-Id` isolation, content/affiliate/
    Pinterest/SEO/analytics/automation contracts, AI OS Bridge validation,
    audit logging, notifications, metrics, OTel, service-to-service auth).
  - `test_failure_recovery.py` — 12 Phase E scenarios (store outages,
    Pinterest timeouts/429/5xx, worker crash, duplicate delivery/webhook,
    retry exhaustion, restart during job) verifying failure → detection →
    retry/fallback → recovery → idempotency → terminal state.
  - `test_observability_checks.py` — Phase G checks (Prometheus targets,
    required metrics, alert rules, Grafana config, Loki logs, OTel, request
    ID propagation, credential absence from logs).
  - `test_load_baselines.py` + `tools/loadtest/baselines.yml` — Phase F
    baseline thresholds (latency/throughput/error-rate budgets; local
    results are not production capacity claims).
  - `test_rollback_plan.py` — Phase I rollback plan validation.
- **Phase G/H/I — Observability, recovery and rollback tooling:**
  - `tools/observability/check-observability.sh` — automated observability
    guard (Prometheus targets, metrics, alerts, Grafana, Loki, OTel).
  - `tools/dev/check-security.sh` — secret patterns, template checks,
    `npm audit`, artifact checks (no secrets in built artifacts).
  - `tools/deploy/rollback-test.sh` — deploy → controlled failure →
    rollback drill with DB compatibility, queue/idempotency and
    row-count verification.
- **Documentation:**
  - `docs/decisions/0014-staging-validation.md` (ADR-0014) and
    `docs/operations/007-staging-validation.md` — completed checks,
    automated evidence, external blockers, required credentials/
    infrastructure/DNS/Vault config, Go/No-Go prerequisites.
  - `docs/operations/002-production-infrastructure.md`,
    `003-disaster-recovery.md`, `004-deployment-and-rollback.md`, and the
    operations README/index updated for the staging pipeline.
  - `libs/backend-core` and `automation-service` versioned to 0.14.0;
    all `atoz-backend-core==0.14.0` pins.

### Fixed

- Deploy pipeline ordering: the image override (`compose.images.yml`) is
  now generated and shipped *before* the migration gate so the gate runs
  inside the exact release images.
- `tools/deploy/write-image-override.sh` no longer emits a `name:` key
  that would silently switch the compose project identity from
  `atozproducthub-staging`/`atozproducthub-prod`.
- `tools/deploy/rollback-test.sh` now generates the immutable image
  override per deployed tag and includes it in the compose command line.
- `tools/deploy/staging-smoke.sh` passes `--env-file` to compose when
  `ENV_FILE` is set (host envs are not exported over SSH).
- `docs/operations/004-deployment-and-rollback.md`: corrected duplicated
  step numbering.


## [0.13.0] - 2026-08-14

### Added

- Implemented M11 Phase 2 (Task 23) — production reliability & launch:
  Phases C–G implemented and verified; Phase H audit framework with the
  30-day reliability and Go/No-Go gates defined (production-time
  checkpoints). ADR-0013 freezes the decisions.
- **Phase C — Secrets & data security:**
  - `libs/backend-core` v0.13.0: the production secrets guard now also
    rejects empty secret fields (`*_secret`, `*_token`, `*_password`,
    `*_api_key`) when `APP_ENV=prod` — no silent defaults.
  - New `atoz_backend_core.security.vault` — guarded `VaultSecretsClient`
    resolving `vault://path?key=field` references (KV v2); strict no-op
    when Vault is not configured; 7 unit tests with mocked transport.
  - Store auth in `infra/docker/compose.prod.yml`: Redis `requirepass`,
    ClickHouse user/password, Kafka SASL_PLAINTEXT (PLAIN mechanism with
    JAAS config); analytics-service Kafka producer passes SASL credentials
    to `AIOKafkaProducer` when configured.
  - `infra/secrets/rotation.md` — rotation cadence, dual-publish window,
    and incident rules for every secret class.
- **Phase D — Observability:**
  - Observability stack in the prod profile: otel-collector, Prometheus,
    Alertmanager, Grafana, Loki, Promtail — configs as code under
    `infra/observability/` (scrape config, SLO alert rules, alertmanager
    routing, Grafana datasource/dashboard provisioning, OTel pipeline,
    Loki retention, Promtail docker-log shipping).
  - automation-service v0.13.0 queue/worker metrics: `atoz_queue_items`,
    `atoz_job_runs`, `atoz_scheduled_jobs_due` gauges on `/metrics` with a
    background refresh that degrades to a warning (2 new tests, incl.
    failure resilience).
  - SLO alert rules: ServiceDown, HighErrorRate (>1% 5xx), SlowP95Latency
    (>500ms), QueueStarvation, QueueFailureSpike, StuckRunningJobs.
- **Phase E — Backup & DR:**
  - `infra/db/backup.sh` (custom-format `pg_dump`, retention, optional
    S3-compatible upload) and `infra/db/restore.sh` (`pg_restore
    --clean --if-exists`, latest-or-explicit dump).
  - New CI `recovery` job: seed → backup → wipe → restore → verify data on
    every push (tested restore, not configured restore).
  - `docs/operations/003-disaster-recovery.md` — RPO/RTO table, DR runbook
    (Postgres/Redis/Kafka/region scenarios), migration recovery.
- **Phase F — Deployment & rollback:**
  - `.github/workflows/deploy.yml` (manual dispatch staging/prod): GHCR
    build+push, migration gate (`alembic upgrade head` before rollout),
    compose rollout, smoke tests (`/healthz` + `/ready`), post-deploy
    verification, and rollback-to-previous-tag on failure.
  - `docs/operations/004-deployment-and-rollback.md` — environment
    promotion, migration gate, database-dependency handling, activation
    prerequisites (self-hosted runner + secrets).
- **Phase G — Reliability & failure injection:**
  - Pinterest client tests: 5xx retry + exhaustion, `httpx` timeout retry
    then success (3 new tests).
  - backend-core `test_readiness.py`: Redis-down readiness returns 503
    degraded (2 new tests).
  - `tools/loadtest/` — Locust reader/operator profile (dev-only, staging).
  - `docs/operations/005-reliability-plan.md` — coverage matrix mapping
    every failure class to its test/evidence.
- **Phase H — Launch audit:** `docs/operations/006-launch-audit.md` —
  security/observability/backup/deployment/performance evidence tables and
  the 30-day reliability validation + Go/No-Go gate criteria.
- Infrastructure guard (`tools/dev/check-infra.sh`) extended: observability
  configs parse + required services/alerts present; backup/restore scripts
  and deploy workflow exist.
- `config/prod/env.template` documents the new store/observability
  variables (REDIS_PASSWORD, CLICKHOUSE_USER/PASSWORD, KAFKA_SASL_*,
  GRAFANA_ADMIN_*).

### Changed

- `libs/backend-core` v0.13.0 and `automation-service` v0.13.0; all
  packages re-pinned to `atoz-backend-core==0.13.0`.
- `infra/docker/compose.prod.yml`: store auth + observability stack
  (24 services), healthchecks for Prometheus/Grafana/Loki.
- `docs/architecture/14-implementation-roadmap.md`: Phase 13 / M8 DoD
  progress for secrets, observability, backup/restore, deployment
  scaffolding, and reliability tests (v0.13.0).
- `README.md`: roadmap status line updated for M11 Phase 2.

## [0.12.0] - 2026-08-14

### Added

- Implemented M11 Production Foundation Phase A + Phase B (production
  audit + infrastructure hardening) — ADR-0012 freezes the hardening
  decisions: non-root images, read-only root filesystems, resource limits,
  trust-zone network isolation, a Caddy TLS edge, and a fail-fast
  production secrets guard.
- `libs/backend-core` v0.12.0: `BaseServiceSettings` now rejects any
  string containing `dev-only-`, `dev-admin`, or `CHANGE_ME` when
  `APP_ENV=prod` (validated recursively through dict/list/tuple fields).
  Dev defaults can no longer reach a live deployment; unit tests cover the
  guard. All service and gateway packages pinned to `atoz-backend-core==0.12.0`.
- `infra/docker/compose.prod.yml`: production deployment profile —
  hardened first-party services (non-root, `read_only: true`, tmpfs
  `/tmp`, `mem_limit`/`cpus`/`pids_limit` + `deploy.resources`), liveness
  `/health` + readiness `/ready` probes (readiness verifies Postgres/Redis),
  trust-zone networks (`edge`/`app`/`data` internal/`integration`), stores
  with no host ports, and zero literal secrets (`${VAR:?...}` fail-fast
  interpolation).
- `infra/docker/caddy/Caddyfile`: Caddy 2 TLS edge — automatic Let's
  Encrypt, HSTS preload, CSP, nosniff/frame/referrer/permissions policies,
  gzip/zstd, `Server` stripping, `/healthz`, and an API route
  (`https://api.<domain>` → gateway). Frontend wiring points commented for
  Phase F (CDN-first track).
- Non-root hardening: all 10 first-party images (`infra/docker/api.Dockerfile`
  + `services/*/Dockerfile`) run as `USER appuser`; content-service
  pre-creates `/data/content` owned by the app user.
- `tools/dev/check-infra.sh`: static infrastructure hardening guard
  (non-root images, prod-compose hardening, network isolation, no host
  ports on services/stores, no `dev-only-`/`CHANGE_ME` literals in the prod
  profile, required interpolation variables documented in
  `config/prod/env.template`, Caddyfile present).
- `config/prod/env.template`: rewritten to document every production
  variable (secrets marked Vault-sourced); the infra guard enforces that
  every `${VAR:?...}` in the prod compose is documented.
- CI: quality job runs the infrastructure guard; docker job validates the
  production compose profile with `docker compose config -q` (all required
  variables exported) and continues to smoke-test the dev compose on the
  hardened images.
- Documentation: `docs/operations/001-production-audit.md` (Phase A audit
  findings A1–A11 with severities and remediation status),
  `docs/operations/002-production-infrastructure.md` (Phase B guide),
  ADR-0012 (indexed in `docs/decisions/README.md`), and
  `infra/docker/README.md` updated for both profiles.

### Changed

- `docs/architecture/14-implementation-roadmap.md`: Phase 13 / M8
  (Production) DoD progress marked for security + infrastructure
  hardening (v0.12.0); remaining follow-ups are observability, backup/DR,
  and deployment workflows (Phases D–F).
- `README.md`: roadmap status line and infrastructure notes updated for
  M11 Phase 1 (audit + hardening).

## [0.11.0] - 2026-08-14

### Added

- Implemented M10 Automation Step 2 (business executors + production
  execution) — ADR-0011 freezes the executor framework: a service-local
  executor registry, short-lived service-to-service JWT for sibling API
  calls, a Redis single-scheduler Beat lock, durable-ledger retries, and
  best-effort notifications (no infinite notification retry).
- `services/automation-service` v0.11.0:
  - Executor framework: `Executor` interface + thread-safe
    `ExecutorRegistry` (name-keyed with `by_queue` lookup), execution
    context with timeout/cancellation, idempotency enforcement, and
    per-executor success/failure handling.
  - Business executors (thin orchestration over owning sibling services —
    no duplicated business logic, no AI):
    - `pinterest.publish_due` — publishes due queued Pins through
      `services/pinterest-service` (niche-scoped claim + publish), safe
      retry of transient failures.
    - `seo.sitemap_rebuild` — triggers sitemap rebuild jobs and tracks
      completion/failure.
    - `affiliate.reconciliation` — triggers affiliate reconciliation and
      records results.
    - `analytics.rollup` — triggers scheduled report/rollup jobs and
      tracks results.
    - `aios.dispatch` — dispatches AI OS jobs through the AI OS Bridge
      only (`services/aios-bridge`); no AI implementation inside
      automation-service.
  - Workflow engine: ledger claim → resolve → execute → persist/requeue/
    terminal → notify; late-ack idempotent redelivery; timeout and
    cancellation handling; job-start event published; scheduled-job
    enqueue with optional override configuration payload.
  - Real Celery wiring: `automation.run_executor` and
    `automation.beat_tick` tasks (`acks_late`, bounded retries/backoff),
    queue routing (`automation`/`celery`), 60-second `beat_schedule`, and
    sync entry points with injected session/event bus for tests.
  - Beat: DB-driven single-scheduler tick with Redis `SET NX EX` lock and
    croniter UTC scheduling (`next_cron_run`), guarding against duplicate
    periodic tasks in multi-scheduler production.
  - Notifications: job started/succeeded/failed/retry-scheduled events
    routed to the admin internal notification channel with delivery-state
    tracking (best-effort, no infinite retry).
  - Admin API additions under `/api/v1/admin`: executor catalog,
    scheduled-job run-now (with optional config), detailed job-run view
    (job_key + niche_slug), detailed queue ledger, queue-item retry/cancel,
    and job-run retry.
  - Tests: +44 automation-service tests (executors, workflow state
    machine, beat locking/scheduling, Celery wiring, ops API, idempotent
    redelivery, timeout/cancellation, retry-to-max, 10-niche isolation).
- `services/pinterest-service`: `claim_due` / `publish_due` accept an
  optional `niche_id` filter so automation can publish a single niche
  (`POST /api/v1/admin/queue/publish-due?limit=&niche_id=`).
- `services/aios-bridge`: new `POST /bridge/jobs` endpoint — maps the
  business automation contract to the AI OS `job_type`, builds a frozen
  `AIOS.Job.Request` (UUID `request_id`, internal callback URL), and
  delegates to `AiosBridgeClient`; contract schemas + typed errors; no AI
  logic in the bridge.
- `services/admin-service`: internal notification channel
  (`POST /api/v1/admin/internal/notifications`, service-account JWT +
  optional internal token) for automation job events.
- Frontend (apps/admin): `/automation` is now functional — Rules
  (enable/disable), Scheduled jobs (run-now), Execution history
  (retry/cancel), Queue ledger (retry/cancel), and Executor catalog, all
  via the shared design system and real admin API client
  (`AUTOMATION_API_BASE`) with mock fallback.
- Infrastructure: Docker Compose adds `automation-worker` (Celery
  `-Q automation,celery`, concurrency 2, max-tasks-per-child 200) and
  `automation-beat` services.

### Changed

- `docs/architecture/14-implementation-roadmap.md`: Phase 12 status
  updated — M10 complete (foundation + Step 2 business executors,
  production Celery worker/Beat, notifications); remaining follow-ups are
  production-time validations (30-day scheduler reliability, load).
- `README.md`: automation section and roadmap status updated for M10
  Step 2.
- `docs/decisions/README.md`: ADR-0011 indexed.

## [0.10.0] - 2026-08-13

### Added

- Implemented M10 Automation Foundation (Phase 12 Step 1) —
  ADR-0010 freezes automation-service ownership of `automation_db`
  (`automation_niches` local tenancy mirror, `automation_rules`,
  `automation_runs`, `aios_job_records`) and documents the Platform-table
  boundary: `scheduled_jobs`, `job_runs`, and `queue_items` stay
  admin-owned (ADR-0009) and are integrated by identical table mapping,
  never re-created by a competing migration stream.
- `services/automation-service` v0.10.0:
  - Domain layer: rule lifecycle (`disabled → enabled`), append-only run
    history with idempotent triggers (`Idempotency-Key` header + nullable
    `automation_runs.idempotency_key` extension column, ADR-0010), job
    execution state machine (`pending → running → success/failed/cancelled`
    on the Platform tables), durable queue ledger
    (`queued → claimed → done/failed`) with exponential-backoff + jitter
    retry metadata (attempts, max_attempts, next retry time), and
    `aios_job_records` Bridge correlation records (`UNIQUE (job_id,
    contract)` dedupe; metadata only — no prompts, no generated internals,
    per Database Blueprint §5.29).
  - Domain events published for lifecycle changes: `automation:rule-enabled`,
    `automation:rule-disabled`, `automation:run-started/succeeded/failed`,
    `automation:job-enqueued`, `automation:job-queued`,
    `automation:aios-job-created` (all `.v1` envelopes).
  - Repositories/service/API: repository + UoW layer following backend-core
    conventions; `AutomationService` facade with server-side tenancy
    enforcement (optional `X-Niche-Id` header: absent = global
    compartment, present = strict niche compartment; scope mismatches
    resolve as not-found); admin API under `/api/v1/admin` with JWT RBAC
    (`automation:read` / `automation:write`): rules, runs, scheduled jobs,
    job runs, queue ledger, and AI OS job records.
  - Celery scaffold: `celery_app.py` / `celery_worker.py` wired from
    environment (`CELERY_BROKER_URL`, `CELERY_BACKEND_URL`) with
    `acks_late`, `worker_prefetch_multiplier=1`, time limits, and an empty
    `beat_schedule` placeholder — no business tasks yet (Step 2).
  - PostgreSQL migration stream `0001` (`alembic_version_automation`)
    validated on fresh SQLite (tests) and fresh PostgreSQL 16 (CI
    database job: single head, upgrade, schema grep, downgrade +
    re-upgrade).
- Infrastructure: automation-service added to Docker Compose (port 8800,
  Postgres + Redis dependencies, healthcheck); CI `database` job validates
  the automation migration stream; CI `docker` job health-checks
  automation-service.
- Tests: 51 automation-service backend tests — retry/backoff math
  (doubling, cap, exhaustion, jitter bounds, monotonicity), idempotency
  keys, rule state machine + events, idempotent run triggers + append-only
  history, queue claim/complete/fail + retry-to-max, AI OS job dedupe +
  lifecycle + boundary (no AI-internal columns), 10-niche isolation
  (no cross-niche reads or mutations; global compartment separation), API
  auth/RBAC/tenancy-header/idempotent-trigger flows, and
  migration upgrade/downgrade/re-upgrade.

### Changed

- `docs/architecture/14-implementation-roadmap.md`: Phase 12 status updated
  (M10 foundation complete; Step 2 executors and production scheduler
  follow).
- `README.md`: roadmap status line now includes M10 (automation
  foundation); automation service section added under Architecture.
- `docs/decisions/README.md`: ADR-0010 indexed.

## [0.9.0] - 2026-08-12

### Added

- Implemented M9 Admin & Operations Layer (operations milestone) —
  ADR-0009 freezes admin-service ownership of `admin_db` (own Alembic
  version table alongside content/affiliate/pinterest/seo/analytics
  streams), the local niche tenancy mirror for the global admin surface,
  the append-only audit ledger, the RBAC seed policy, the MFA/session
  gate, the operations dashboard, and the HMAC-verified internal event
  ingestion surface.
- `services/admin-service` v0.9.0:
  - Domain layer: `admin_niches` (local mirror), `admin_users`, `roles`,
    `permissions`, `role_permissions`, `user_roles` (niche-scoped
    assignments), `api_keys` (hash-only storage), `admin_preferences`,
    `audit_logs` (append-only, actor/action/resource/niche/request-ID),
    `notifications` + `notification_preferences` + `notification_deliveries`,
    `queue_items` (durable ledger with explicit state transitions),
    `webhook_logs` (idempotent on source+event_id), `operation_logs`,
    `scheduled_jobs`, and `job_runs` — UUIDv7 keys.
  - RBAC: frozen permission catalog + system-role matrix seeded
    idempotently; operator identity CRUD; niche-scoped role
    assign/revoke; effective-permission resolution; MFA provisioning
    endpoint and MFA-verified session gate for privileged actions;
    revocable sessions (in-memory dev/CI, Redis production).
  - Audit: append-only records with server-side actor metadata, search by
    action/entity/actor/niche/request-ID, and capped CSV export with
    `Content-Disposition` download.
  - Ops: `/api/v1/admin/ops/overview|status|isolation` (failure counts,
    per-state queue visibility, sibling-service health probes, tenancy
    verification), queue visibility + safe bounded retry of failed items,
    searchable webhook/operation logs, scheduled-job and job-run
    visibility, notification inbox + preferences.
  - Events: `/api/v1/admin/events/ingest` HMAC-SHA256 verification over
    the raw body (same convention as the analytics webhook), idempotent
    `(source, event_id)` replays, domain-event → operation mapping, and
    payload size limits.
- Frontend (apps/admin): new `/ops` operations dashboard (system status,
  queue, job runs, isolation), `/ops/logs` (operation + webhook logs), and
  `/audit` (searchable append-only audit view) — server components over the
  shared design system with axe-tested accessibility, wired to the real
  admin API via `NEXT_PUBLIC_ADMIN_API_BASE_URL` with mock fallback; nav
  and page titles updated; all pages remain noindex.
- Infrastructure: admin-service added to Docker Compose (port 8700) with
  Postgres dependency and healthcheck; CI `database` job now validates the
  admin migration stream on fresh PostgreSQL 16 (head, schema, downgrade +
  re-upgrade); CI `docker` job health-checks admin-service.
- Tests: 31 admin-service backend tests (RBAC catalog/matrix, permission
  denial, MFA gate, user CRUD + role lifecycle, effective permissions,
  audit append-only/search/export, ops overview/status probes/isolation,
  queue retry safety, webhook signature + idempotency + size limits,
  notifications lifecycle/preferences, niche-scoped isolation, migration
  upgrade/downgrade/re-upgrade on clean DB + single head) plus 3 frontend
  ops/audit page tests with axe; full M1–M8 regression suite remains green.

### Fixed

- Alembic migration streams remain isolated per service via dedicated
  version tables (extended to the admin stream).
- Anchored the `.gitignore` `logs/` rule to the repository root so the
  admin `ops/logs` frontend route is tracked instead of silently ignored
  (the unanchored pattern also skipped the route file, breaking the CI
  typecheck step).
- Made the startup RBAC seed resilient when the admin schema has not been
  migrated yet (compose dev boot): a missing-table error logs a warning and
  the service stays healthy; readiness probes still report DB health
  independently.

## [0.8.0] - 2026-08-11

### Added

- Implemented M8 Analytics Business Layer (measurement milestone) —
  ADR-0008 freezes analytics-service ownership of `analytics_db` (own
  Alembic version table alongside content/affiliate/pinterest/seo
  streams), the local niche tenancy mirror, the append-only event ledger
  with unique `event_id` idempotency, the PostgreSQL → Kafka → ClickHouse
  event pipeline, daily/weekly rollups into read models, and the AI OS
  boundary where insights are read-only attributed data that can arrive
  only through the AI OS Bridge.
- `services/analytics-service` v0.8.0:
  - Domain layer: `analytics_niches` (local mirror), `analytics_event_ledger`
    (append-only, unique `event_id`, `niche_id` + optional
    `pinterest_account_id`), `traffic_daily`, `visitor_daily`,
    `daily_metrics`, and `kpi_snapshots` — every business record carries
    `niche_id`; Pinterest rows carry `pinterest_account_id` so 10 accounts
    never mix; UUIDv7 keys.
  - Pipeline: `EventBackbone`/`Warehouse` ABCs with in-memory dev/CI
    implementations and lazy Kafka (`KAFKA_ENABLED=true`) and ClickHouse
    (`WAREHOUSE_ENABLED=true`) transports; a `PipelineWorker` drains the
    backbone into the warehouse.
  - Collector: `/collect/v1/events` and `/collect/v1/events/batch` with
    slug-based niche tenancy, `event_id` idempotency, per-item batch
    failure isolation, server-side timestamps, size limits, and a
    sensitive-trait guard (email/phone/password/ssn/credit_card/token/
    authorization/api_key traits are rejected).
  - Webhook: `/webhooks/v1/analytics/events` HMAC-SHA256 verified with the
    shared `event_webhook_secret`; maps `content:*`, `pin:*`, `product:*`,
    `affiliate:click`, `revenue:attributed`, and `seo:sitemap-rebuilt`
    domain events into internal analytics events; unknown types rejected.
  - Service layer: `AnalyticsService` facade with niche mirror CRUD,
    idempotent ingest, rollups (daily + weekly on Sundays, idempotent
    upserts), traffic/visitor/metrics/top-pages/overview/events/KPI reads,
    and pipeline status. Domain event: `analytics:rollup-completed.v1`.
  - API: read-only admin API (`/api/v1/admin/*` with JWT RBAC
    `analytics:read`/`analytics:write` + mandatory `X-Niche-Id`).
- Analytics dashboard (`apps/admin`): the analytics and revenue pages now
  connect to the live analytics API via the typed `api.analytics.*` client
  namespace when `NEXT_PUBLIC_ANALYTICS_API_BASE_URL` is set — KPI cards
  (sessions, pageviews, visitors, bounce rate, affiliate clicks,
  conversions, revenue, pin clicks), weekly session chart, traffic-source
  donut, affiliate/revenue metric chart, and top-pages table, with
  server-driven date-range filters (`?range=30d|90d|ytd`). Mock fixtures
  remain the standalone default.
- Tests: collector validation/idempotency/sensitive-data guard, batch
  isolation, webhook signature verification + idempotency + unknown-type
  rejection, rollup correctness, pipeline draining, repository append-only
  enforcement, admin API RBAC, cross-niche and cross-account isolation
  (10 simulated accounts), migration upgrade/downgrade/re-upgrade, and
  HTTP-level tenancy.
- Docker Compose: `analytics-service` (port 8600) plus a single-node
  KRaft Kafka and ClickHouse with healthchecks; CI builds the image,
  smoke-tests `/health`, and validates the analytics migration stream
  against fresh PostgreSQL 16 (upgrade, schema verification,
  downgrade/re-upgrade).
- CI: the workflow was validated with `actionlint` against official GitHub
  Actions conventions.

### Security

- The analytics-service dependency tree is AI-free (no-AI CI guard +
  pip-audit); webhook signatures are verified before any state change;
  collector traits are filtered for sensitive keys before persistence; the
  ledger is append-only (no update/delete paths); tokens and credentials
  never appear in responses or logs.

## [0.7.0] - 2026-08-11

### Added

- Implemented M7 SEO & Discovery Layer (findability milestone) — ADR-0007
  freezes seo-service ownership of `seo_db` (own Alembic version table
  alongside content/affiliate/pinterest streams), the local niche tenancy
  mirror, niche-global URL slug uniqueness plus database-level
  `UNIQUE (niche_id, path)`, event-driven Typesense search indexing
  (lexical only — PostgreSQL stays the source of truth), and the AI OS
  boundary where SEO metadata intelligence arrives only through the AI OS
  Bridge.
- `services/seo-service` v0.7.0:
  - Domain layer: `seo_niches` (local mirror), `url_registry`,
    `seo_metadata`, `sitemap_shards`, `seo_crawl_reports`, and
    `seo_health_checks` — every business record carries `niche_id`;
    composite unique constraints prevent duplicate paths/slugs per niche;
    UUIDv7 keys.
  - Repository layer: niche-scoped repositories and a `SeoUnitOfWork`
    mirroring the content/affiliate/pinterest conventions.
  - Service layer: `SeoService` facade with niche mirror CRUD, URL
    registration + duplicate prevention (path- and slug-level), metadata
    upsert/read-back, event-driven index/de-index, sitemap group rebuild +
    shard rendering, robots rendering (Pinterestbot + image proxy never
    blocked), crawl-report records, health checks, JSON-LD builders, and a
    `SearchIndex` ABC with a Typesense client and an in-memory dev/test
    implementation. Domain events: `seo:sitemap-rebuilt.v1`,
    `search:indexed.v1`, `search:removed.v1`.
  - API: read-only public API (`/api/v1/public/seo/{meta,robots,sitemaps}`
    and `/api/v1/public/search` by niche slug), admin API (`/api/v1/admin/*`
    with JWT RBAC `seo:read`/`seo:write` + mandatory `X-Niche-Id`), and the
    HMAC-verified event webhook (`/webhooks/v1/seo/events`).
- Search: niche-scoped article/category/tag/product search with
  pagination, type filters, and explicit cross-niche isolation tests; no
  vectors, embeddings, or AI ranking.
- Sitemaps: per-group sharding and indexes for articles, categories, tags,
  products, Pinterest landing pages, and affiliate collections; XML
  validation in tests; only active public URLs; private URLs never exposed.
- robots.txt: Googlebot/Bingbot/Pinterestbot allowed; admin, API, search,
  internal, and private paths blocked; Pinterest image proxy compatible.
- Google/Bing integration boundaries: GSC/Bing crawl-report storage and a
  sitemap-submission boundary with server-side-only credential refs; mocked
  in tests, no live credentials required.
- Frontend: `apps/web` SEO namespace wired to the live SEO public API via
  `NEXT_PUBLIC_SEO_API_BASE_URL` — real niche-scoped search results,
  applied metadata + JSON-LD (Article/Product), canonical/robots handling,
  and site-origin proxies for `/robots.txt`, `/sitemap.xml`, and
  `/sitemaps/{group}-{n}.xml` with strict filename validation; admin pages
  remain noindex.
- Docker Compose: `seo-service` (port 8500) and `typesense` (port 8108)
  with healthchecks; CI builds the image, smoke-tests `/health`, validates
  the SEO migration stream against fresh PostgreSQL 16 (upgrade,
  downgrade/re-upgrade, schema verification), and adds a Lighthouse
  Core Web Vitals + SEO gate against the built web app.

### Security

- The seo-service dependency tree is AI-free (no-AI CI guard + pip-audit);
  webhook signatures are verified before any state change; sitemap proxies
  whitelist group names and numeric shards only.

## [0.6.0] - 2026-08-10

## [0.6.0] - 2026-08-10

### Added

- Implemented M6 Pinterest Business Layer (traffic milestone) — ADR-0006
  freezes pinterest-service ownership of `pinterest_db` (own Alembic
  version table alongside content/affiliate streams), the local niche
  tenancy mirror, mandatory `niche_id` + `pinterest_account_id` dual
  scoping, Vault-bound token storage (token VALUES never enter the
  database), OAuth 2.0 authorization-code + PKCE + per-account state/CSRF,
  per-account `org_read`/`org_write` rate limiting, queue-based publishing
  with idempotency + retry, append-only publishing-attempt ledger, and
  per-account analytics as business data only.
- `services/pinterest-service` v0.6.0:
  - Domain layer: `pinterest_niches` (local mirror), `pinterest_accounts`,
    `pinterest_tokens` (Vault refs + expiry metadata only),
    `pinterest_boards`, `board_sections`, `pinterest_pins` (append-only
    ledger), `pin_queue_items`, `pin_publish_attempts`, and
    `pinterest_analytics` — every account-scoped record carries `niche_id`
    AND `pinterest_account_id`; composite unique constraints prevent
    cross-account/cross-niche duplicates; UUIDv7 keys.
  - Repository layer: account-scoped repositories that reject any
    account-scoped query without account context (`AccountIsolationError`),
    append-only pin ledger (no delete path), composite-unique checksum
    dedupe per account, and a typed `PinterestUnitOfWork`.
  - Service layer: `PinterestService` facade with niche mirror CRUD,
    per-account CRUD, `start_connect`/`complete_connect` OAuth flow
    (state verification + double CSRF binding + PKCE + token exchange +
    Vault write), `disconnect_account` (soft revoke), token refresh with
    60s expiry margin + refresh-token rotation, board/section sync,
    pin draft → enqueue → publish lifecycle (`publish_due` worker entry
    point), cancel, per-account analytics upsert, and public reads.
    Domain events: `pin:scheduled.v1`, `pin:published.v1`, `pin:failed.v1`,
    `account:connected.v1`, `account:disconnected.v1`.
  - Typed Pinterest API v5 client: boards CRUD, board sections, pins
    create/read/delete, bookmark pagination, 401-refresh-and-retry once,
    401/403/429/5xx classification, exponential backoff + full jitter,
    `Retry-After` honored, per-account token buckets by category (never a
    global limiter).
  - Alembic migration `0001` (portable SQLite/PostgreSQL) with all
    blueprint indexes, unique constraints, and FKs; CI validates the
    Pinterest migration stream against the same fresh PostgreSQL 16 used
    for content and affiliate, including downgrade/re-upgrade.
  - API: read-only public API (`/api/v1/public/{accounts,boards,pins}` by
    niche slug), admin API (`/api/v1/admin/*` with JWT RBAC
    `pinterest:read`/`pinterest:write` + mandatory `X-Niche-Id`), and the
    OAuth callback (`/oauth/callback`). Token VALUES never appear in
    responses or logs.
- Docker Compose: `pinterest-service` (port 8400) with Postgres dependency
  and healthcheck; CI builds the image and smoke-tests `/health`.
- Frontend: `apps/web` Pinterest namespace wired to the live public
  Pinterest API via `NEXT_PUBLIC_PINTEREST_API_BASE_URL` (mock-fixture
  fallback); `apps/admin` Pinterest screen shows accounts + pin queue with
  per-account rate-limit status.
- Docs: ADR-0006 freezes the Pinterest architecture decisions; README,
  implementation roadmap (Phase 8 + M5 milestone), and this changelog
  updated. No AI functionality was introduced; the no-AI guard, contract
  validation, and dependency audit remain green.

## [0.5.0] - 2026-08-10

### Added

- Implemented M5 Affiliate Engine (monetization milestone) — ADR-0005 freezes
  affiliate-service ownership of `affiliate_db`, the local niche tenancy
  mirror (cross-database FKs to `content_db.niches` are impossible), the
  server-controlled signed redirect rule, append-only click/conversion
  ledgers, webhook signature verification + idempotent conversion ingestion,
  and disclosure enforcement in the business layer.
- `services/affiliate-service` v0.5.0:
  - Domain layer: `affiliate_niches` (local mirror), `affiliate_networks`
    (global reference), `affiliate_merchants`, `affiliate_products`,
    `product_categories` + `product_category_links`, `affiliate_links`,
    `link_tokens`, `affiliate_clicks`, `click_attributions`,
    `revenue_transactions`, `revenue_reconciliations`, `revenue_summaries`,
    and `affiliate_webhook_logs` — every business record niche-scoped by
    `niche_id`; UUIDv7 keys; HMAC-SHA256 token signing; commission lifecycle
    state machine (pending → approved → paid, pending → rejected).
  - Repository layer: niche-scoped repositories (every query/mutation
    carries `niche_id`), append-only click/revenue ledgers (no update/delete
    paths), `UNIQUE (network_id, network_transaction_id)` conversion
    idempotency, webhook-log correlation by `(source, event_id)`, and a typed
    `AffiliateUnitOfWork`.
  - Service layer: `AffiliateService` facade with network/merchant/product/
    category/link/token CRUD, product activation gated on disclosure-required
    links, signed token minting/revocation, `resolve_redirect` (invalid,
    revoked, expired tokens → indistinguishable 404; click recorded before
    redirect), `process_conversion` webhook ingestion (HMAC verification,
    schema validation, idempotent + transactional, domain events after
    commit), `transition_commission`, revenue summaries/dashboard, and
    reconciliation records. Domain events: `affiliate:click.v1`,
    `revenue:attributed.v1`, `product:removed.v1`.
  - Alembic migration `0001` (portable SQLite/PostgreSQL, `sa.false()/true()`
    defaults per the M4 Postgres lesson) with all blueprint indexes, unique
    constraints, and FKs; CI validates both content and affiliate migration
    streams against the same fresh PostgreSQL 16.
  - API: public read API (`/api/v1/public/{product-categories,products}` +
    `/api/v1/public/go/{token}` redirect resolver), admin API
    (`/api/v1/admin/{networks,merchants,product-categories,products,links,
    tokens,clicks,revenue,revenue-summaries,reconciliations}` with JWT RBAC
    `affiliate:read`/`affiliate:write` + mandatory `X-Niche-Id`), and the
    webhook receiver `POST /webhooks/v1/{network_code}/conversion`
    (202 fast-ack incl. duplicates; 400 problem+json on invalid
    signature/payload).
- Admin affiliate screens in `apps/admin` (shared design system): overview
  with revenue KPIs, networks, merchants, products, links, clicks,
  conversions & commissions (status filter + approve/reject/mark-paid),
  and reconciliation — wired to the affiliate admin API when
  `NEXT_PUBLIC_AFFILIATE_API_BASE_URL` is set, mock-fixture fallback
  otherwise; nested admin sidebar navigation for the affiliate module.
- Public site (`apps/web`): product and collection pages connected to the
  live affiliate public API (DTO mapping, absolute go URL); new
  `AffiliateBuyButton` client component that resolves the server-controlled
  `/go/{token}` endpoint and redirects only after success, with
  `rel="sponsored nofollow"` and double-click protection; disclosure badge
  driven by the business layer's `disclosure_required` flag.
- Shared core: `atoz_backend_core.uuids` (UUIDv7) and
  `atoz_backend_core.slug` (slugify + unique slug) added; content-service
  re-exports them so M4 tests stay green; all services pinned to
  `atoz-backend-core==0.4.0`.
- Infrastructure: `affiliate-service` added to `infra/docker/compose.yml`
  (Postgres-backed, healthchecked, port 8300); CI database job now verifies
  the affiliate migration head, upgrade, schema smoke (`\dt`), and
  downgrade/re-upgrade on fresh PostgreSQL; Docker job adds the
  affiliate-service compose health check.
- Tests: 61 new backend tests (network/merchant/product/offer CRUD, link
  signing/validation, redirect security, disabled/expired/revoked links,
  open-redirect prevention, click recording, webhook signature + idempotency,
  duplicate suppression, commission lifecycle, revenue attribution,
  disclosure enforcement, RBAC, cross-niche isolation at repository/service/
  HTTP level, migration upgrade/downgrade) — 215 total across the repo; 7 new
  frontend tests (web live-affiliate-client mapping + admin affiliate screens
  with axe WCAG checks) — 37 total (web 13, admin 16, design-system 8). No-AI guard, contract validation, ruff,
  mypy, pip-audit, typecheck, lint, and production builds all green.

### Security

- Redirect resolver never trusts a browser-supplied destination URL; only
  stored affiliate-link records resolved through HMAC-signed tokens.
- Conversion webhooks require network-specific HMAC signatures; invalid
  signatures are rejected before any database write; repeated delivery
  cannot create duplicate commission records (unique constraint + event-log
  correlation).
- Affiliate admin routes require a valid gateway-issued JWT with
  `affiliate:read`/`affiliate:write` claims plus a valid `X-Niche-Id`; dev
  JWT, webhook, and token-signing secrets are local/test-only (production via
  Vault). No network credentials are exposed to frontend clients.

## [0.4.0] - 2026-08-09

### Added

- Implemented M4 CMS business layer (first business milestone) — ADR-0004
  freezes content-service ownership of `content_db`, the lifecycle status
  superset (draft → review → published → archived + unpublished + re-publish),
  the immutable published-snapshot rule, `X-Niche-Id` tenancy transport, and
  deferred partitioning.
- `services/content-service` v0.4.0:
  - Domain layer: statuses (`ArticleStatus`, taxonomy statuses), server-side
    lifecycle state machine (`domain/lifecycle.py`), slugify + per-niche
    `unique_slug`, RFC7807 error hierarchy, UUIDv7 keys, SQLAlchemy entities
    for niches/articles/article_versions/categories/article_categories/tags/
    article_tags — every content table scoped by `niche_id`.
  - Repository layer: niche-scoped repositories (every query/mutation carries
    `niche_id`), slug uniqueness, soft delete, link-table replace helpers, and
    a typed `ContentUnitOfWork`.
  - Service layer: `ContentService` facade with CRUD, lifecycle validation,
    immutable versioning, published-snapshot protection (edits while
    published keep the live snapshot until re-publish), author/editor
    metadata, taxonomy validation, and domain events (`content:published.v1`,
    `content:updated.v1`, `content:unpublished.v1`) emitted after commit.
  - Content storage abstraction (`ContentStore`, local + in-memory) with
    SHA-256 checksums; bodies live outside the database (DB Blueprint §2.1).
  - Alembic migration `0001` (portable SQLite/PostgreSQL) with all blueprint
    indexes/unique constraints; CI validates it on a fresh PostgreSQL 16.
  - API: public read API (`/api/v1/public/{niches,articles,categories,tags}`,
    published-only, niche-by-slug) and admin API (`/api/v1/admin/*` with
    JWT RBAC `content:read`/`content:write` + mandatory `X-Niche-Id`),
    17 OpenAPI paths.
- Admin CMS screens in `apps/admin`: content list with status filter,
  new-article form, article editor with lifecycle actions and version
  history — built on the shared design system, wired to the content-service
  admin API via the typed client when `NEXT_PUBLIC_CONTENT_API_BASE_URL` is
  set, mock-fixture fallback otherwise (default CI build mode).
- Public site (`apps/web`): the content namespace of the typed API client now
  reads the real public API when `NEXT_PUBLIC_CONTENT_API_BASE_URL` is set
  (mapped to existing page shapes); article/category/tag pages unchanged and
  still fully mock-backed in the default build.
- Infrastructure: `content-service` added to `infra/docker/compose.yml`
  (Postgres-backed, healthchecked); CI gains a `database` job (fresh
  PostgreSQL, single-head check, upgrade/downgrade/re-upgrade, schema smoke)
  and a compose health check for content-service.
- Tests: 58 new tests (unit, repository, service/domain, public/admin API,
  lifecycle, authorization, slug uniqueness, versioning, published-snapshot
  immutability, cross-niche isolation, migration/clean-database) — 154 total
  across the repo; 9 new frontend tests (web live-client mapping + admin CMS
  screens with axe WCAG checks) — 22 total. No-AI guard, contract validation,
  ruff, mypy, pip-audit, typecheck, lint, and production builds all green.

### Security

- Admin content routes require a valid gateway-issued JWT with
  `content:read`/`content:write` claims plus a valid `X-Niche-Id`; the dev
  JWT secret is local/test-only (production via Vault).

## [0.3.0] - 2026-08-08

### Added

- Implemented M3 backend business foundation (first backend code beyond M1):
  - ADR-0002: accepted `services/automation-service/` as the eighth service skeleton (business automation workflows, not AI OS automation).
  - ADR-0003: accepted `libs/backend-core` (`atoz-backend-core`) as the shared backend foundation consumed by the gateway and every service.
  - `libs/backend-core`: shared infrastructure primitives — pydantic-settings base config, JSON structured logging with request-ID correlation, middleware (request ID, security headers, rate limiting with 429 + `Retry-After`), async PostgreSQL/Redis engines + health checks, ORM `Base`, repository pattern + unit of work, domain event system (`type.v1` envelope, in-memory bus, publisher), Celery worker scaffolding, auth primitives (JWT access/refresh, RBAC, sessions, Argon2 password hashing, MFA provisioning placeholders), secrets loading (env + Vault KV v2 hooks), Prometheus metrics, OpenTelemetry hooks (no-op unless enabled), and `create_service_app` FastAPI factory (`/health`, `/ready`, `/metrics`). Per-service Alembic migration template under `libs/backend-core/migrations/`.
  - `libs/contracts/aios/`: frozen v1 JSON Schemas for all seven AI OS contracts (`AIOS.Content.Intake`, `AIOS.Job.Request`, `AIOS.Job.Status`, `AIOS.SEO.Metadata`, `AIOS.Pinterest.Assets`, `AIOS.Analytics.Insights`, `AIOS.Heartbeat`) — validated by the Bridge and CI.
  - `services/aios-bridge/`: the only AI OS contact point — transport-only client with schema-first contract validation, HMAC-SHA256 request signing, exponential-backoff retries (1s × 2, cap 60s, max 5), timeout, heartbeat, and a circuit-breaker stub. No prompts, models, generation, learning, or memory.
  - Seven service skeletons (`content`, `affiliate`, `pinterest`, `seo`, `analytics`, `admin`, `automation`): per-service package, shared-app factory wiring, health/readiness/metrics endpoints, tests, per-service `db/migrations/`, Dockerfiles, READMEs. No business logic.
  - Gateway (`apps/api`) upgraded to v0.3.0: consumes the shared factory, adds `/ready` and `/metrics`, `AuthMiddleware` (Bearer decode + session resolution → `request.state.auth`), and the versioned API v1 router (`/api/v1/auth/token`, `/auth/refresh`, `/auth/revoke`, `/auth/me`) with a dev credential placeholder disabled in production (OIDC replaces it in Phase 5).
  - Tooling: `Makefile setup` installs backend-core, gateway, and all services; root pytest/mypy/ruff config covers the new trees; CI quality/test jobs install every package; Docker job builds all service images; compose adds `aios-bridge` with a health check; `config/{dev,staging,prod}/env.template` added.
  - 99 tests passing across gateway (25), backend-core (33), aios-bridge (20), and the seven service skeletons (21) — plus lint, type check, no-AI guard, and contract validation.

### Removed

- Duplicated M1 logging/middleware implementations in the gateway are now thin re-exports of the shared backend-core implementation (ADR-0003).

### Security

- Dev-only JWT secret and dev-admin credential placeholder are local/test-only and explicitly disabled when `APP_ENV=prod`; production secrets come from Vault.

## [0.2.0] - 2026-08-07

### Added

- Implemented M2 frontend foundation (first frontend code):
  - ADR-0001: accepted a shared design-system workspace (`libs/design-system`, package `@atoz/design-system`) with the required ADR + contract-compliance review per Folder Blueprint §6.4.
  - `libs/design-system`: design tokens (color/typography/spacing/breakpoints per UI/UX Design System §3–§8, Tailwind v4 `@theme` with runtime light/dark variables), theme provider (light/dark/system, persisted, pre-paint script), and core components (Button, Badge, Card, Container, Header, Footer, Hero, Prose, Breadcrumbs, Pagination, Form fields, Search, Filters, Table with mobile card-list fallback, Notifications, EmptyState, DisclosureBadge, KPI cards, ContentCard, Avatar, Recharts chart wrappers with accessible data-table fallbacks).
  - `apps/web` (@atoz/web): public website scaffold (Next.js App Router, TypeScript strict, Tailwind) with wireframe pages for all 15 public pages from Design System §11.2 (home, article, category, tag, search, product, Pinterest landing, affiliate collection, about, contact, privacy, terms, disclaimer, sitemap, 404) rendered from a typed API-client stub over static mock data.
  - `apps/admin` (@atoz/admin): admin dashboard scaffold with app-shell (sidebar + topbar) and wireframe pages for all 7 admin pages (login, dashboard, analytics, revenue, Pinterest, automation, settings), all `noindex`.
  - Workspace tooling: root `package.json` workspaces (`apps/*`, `libs/design-system`), per-app ESLint (eslint-config-next flat), `tsc --noEmit` typecheck, `next build` for both apps, vitest + @testing-library/react + axe-core tests (21 passing, WCAG 2.1 AA checks).
  - CI: new `frontend` job (npm ci, lint, typecheck, build, tests) on Node 22; existing Python jobs unchanged.
  - `Makefile`: added `fe-install`, `fe-lint`, `fe-typecheck`, `fe-build`, `fe-test`, `fe-check` targets.
- M2 contains no business features: no articles CMS, affiliate engine, Pinterest API, SEO service, analytics collection, authentication, or AI functionality. All content is static wireframe mock data; real data arrives in Phases 3–11 through the API gateway and `libs/contracts`.

## [0.1.0] - 2026-08-07

### Added

- Implemented M1 foundation setup (first code):
  - Monorepo scaffold per Folder Blueprint §3 (apps, services, libs, config, infra, assets, pipelines, tests, tools, docs) with README stubs.
  - Root tooling: `Makefile`, `pyproject.toml` (ruff, mypy, pytest), `.editorconfig`, `.env.example`, `package.json`, updated `.gitignore` and `.dockerignore`.
  - API gateway foundation (`apps/api`, FastAPI): pydantic-settings configuration with environment loading, structured JSON logging, RFC 7807 problem+json error handling, request-context middleware (X-Request-ID), and the `/health` endpoint.
  - Docker: `infra/docker/api.Dockerfile` and `infra/docker/compose.yml` (api, postgres, redis) with healthchecks.
  - GitHub Actions CI: quality (ruff lint, format check, mypy), tests (pytest), Docker build + compose smoke, gitleaks secret scan.
  - No-AI guard (`tools/dev/check-no-ai.sh`) enforcing Website Architecture Contract §4.2 and Folder Blueprint §6.1.
- M1 contains no business logic: no Pinterest, affiliate, SEO, analytics, authentication, or AI functionality.

### Added

- Initial repository creation with professional documentation:
  - `README.md` covering project vision, goals, scope, repository rules, architecture philosophy, the relationship with the Universal AI Content Operating System, the "No Duplicate Features" policy, development rules, and the future roadmap.
  - `LICENSE` (MIT).
  - `.gitignore` baseline for a clean web-project workspace.
  - `CONTRIBUTING.md` with contribution guidelines and repository boundaries.
- Repository governance: business-layer only, fully separate from the Universal AI Content Operating System.
- Added the complete website architecture documentation set under `docs/architecture/`:
  - Overview, design principles, system context, and scale targets.
  - Folder structure, system layers, and module boundaries.
  - Data flow, API flow, responsibilities, security boundaries, and deployment strategy.
  - Boundaries with the Universal AI Content Operating System defined for every layer and module.
- Added the binding Website Architecture Contract (`docs/architecture/09-website-architecture-contract.md`):
  - Locked statement: the website is a business platform only; all intelligence belongs to the AI OS.
- Expanded `01-folder-structure.md` into the permanent project folder blueprint:
  - Complete directory tree with every folder's purpose, responsibility, owner, and future modules.
  - Category map (frontend, backend, database, APIs, documentation, configuration, infrastructure, assets, SEO, affiliate, Pinterest, analytics, admin, automation, testing).
  - Repository conventions (naming, imports, dependencies) and technology placement (Next.js, FastAPI, PostgreSQL, Redis, Docker, CI/CD, AI OS Bridge).
  - Verification against the Website Architecture Contract and no-AI-duplication checks.
- Added the permanent technology specification (`docs/architecture/10-technology-stack.md`):
  - Frozen stack for frontend, backend, database, infrastructure, SEO, Pinterest, affiliate, analytics, security, admin dashboard, and AI OS Bridge.
  - Every technology justified: why selected, alternatives rejected, scalability, cost, free tier, production readiness.
  - Final stack table (Technology | Purpose | Status | Future Replacement) and forbidden-technology boundary.
- Added the permanent production database blueprint (`docs/architecture/11-database-architecture.md`):
  - Database philosophy, store topology (PostgreSQL, ClickHouse, Redis, Typesense, R2), and ERD.
  - 40+ tables across all groups (niches, Pinterest accounts/boards/pins, articles, categories, tags, affiliate, SEO, traffic, analytics, revenue, click tracking, users, admin, roles, permissions, automation, scheduler, queue, logs, audit, notifications, media, settings) with purpose, keys, fields, indexes, relationships, ownership.
  - Mandatory niche/Pinterest-account isolation rules, partition/archive/backup/caching/search/analytics strategies, and read/write/delete/restore flows.
  - Verification that no AI Content OS data lives in this database.
- Added the frozen API contract specification (`docs/architecture/12-api-contracts.md`):
  - AI OS Bridge contracts (Content Intake, Job Request/Status, SEO Metadata, Pinterest Assets, Analytics Insights, Heartbeat).
  - Authentication, versioning, error model, rate limits, retry policy, idempotency, webhook and event contracts.
  - Locked rule: website never calls Gemini/OpenAI/Claude directly; only Website → AI OS Bridge → AI OS.
- Added the permanent UI/UX design system (`docs/architecture/13-ui-ux-design-system.md`):
  - Design philosophy, brand identity, color system, typography, icons, layout, grid, spacing, component and responsive rules.
  - All 22 pages with wireframes, user journeys, components, and SEO/Pinterest/affiliate/analytics importance.
  - Shared components, accessibility (WCAG 2.1 AA), SEO layout, Core Web Vitals budgets, device experience, and no-AI-in-UI verification.
- Added the master implementation roadmap (`docs/architecture/14-implementation-roadmap.md`):
  - 13 phases (Repository Setup → Production Deployment) with goal, scope, deliverables, dependencies, complexity, risk, success criteria.
  - Module details per phase: files, folders, dependencies, database tables, API contracts, future integrations, testing.
  - Dependency-ordered implementation sequence, milestone roadmap M1–M8 with Definition of Done for each.
  - Closed-loop definition, locked boundaries, prohibitions, and amendment/ratification process.
