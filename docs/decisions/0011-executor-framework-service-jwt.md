# ADR-0011 — Executor Framework, Service-to-Service JWT, and Single-Scheduler Beat

- **Status:** Accepted
- **Date:** 2026-08-14
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 03-module-boundaries.md, 05-api-flow.md, 07-security-boundaries.md, 11-database-architecture.md (annotations), 12-api-contracts.md, 14-implementation-roadmap.md, CHANGELOG.md

## Context

Task 21 (M10 Phase 12 Step 2) turns the automation foundation (v0.10.0,
ADR-0010) into a working execution engine: business executors call owning
sibling services, Celery workers consume the durable queue ledger, Beat
wakes a DB-driven scheduler, and the admin dashboard operates rules, jobs,
runs, and queue items. Four architectural decisions must be frozen before
implementation:

1. **Executor dispatch:** the durable `queue_items` ledger stores a business
   `queue` (e.g. `seo`, `pinterest`) while executors are registered by
   stable **name** (e.g. `seo.sitemap_rebuild`). The worker must resolve
   the right executor for a queue item without embedding business logic in
   Celery tasks.
2. **Cross-service authentication:** executors call sibling admin APIs
   (Pinterest publish, sitemap rebuild, affiliate reconciliation, analytics
   rollups, admin notifications). Each service verifies JWTs against its
   own secret; the automation worker must mint short-lived service tokens.
3. **Single-scheduler Beat:** Celery docs warn that multiple Beat
   processes produce duplicate periodic tasks; the schedule must have one
   owner.
4. **Retry ownership:** Celery late acks can redeliver a task after a
   worker crash; unbounded `autoretry_for` would fight the durable ledger's
   exponential-backoff policy.

## Decision

1. **Executor abstraction + registry.** `services/automation-service`
   defines an `Executor` ABC (`name`, `queue`, `async execute(ctx)`), a
   thread-safe `ExecutorRegistry` keyed by name with a `by_queue` lookup,
   and five built-in executors: `pinterest.publish_due`,
   `seo.sitemap_rebuild`, `affiliate.reconciliation`,
   `analytics.rollup`, `aios.dispatch`. The execution workflow resolves the
   executor by (a) explicit task argument, (b) the item's queue, (c) the
   scheduled job's `handler`, then (d) registry `by_queue` — no executor
   lookup is embedded in Celery tasks.
2. **Executors are thin HTTP clients.** Every executor calls the owning
   sibling service's frozen admin API; automation-service never
   re-implements Pinterest/SEO/affiliate/analytics/AI OS logic (Website
   Contract §4). Tenancy is forwarded as `X-Niche-Id` on every sibling
   call; the AI OS Bridge (`/bridge/jobs`) is the only AI OS contact point
   and remains transport-only (contract validation, signing, retry,
   circuit breaker).
3. **Service-to-service JWT.** `SiblingClients` mints a short-lived access
   token per sibling using that sibling's configured `*_jwt_secret`
   (subject `automation-service`, session id `svc:<service>`, the
   sibling's write permission). Secrets come from environment/Vault, never
   from the frontend. The admin internal notification channel also guards
   with an optional `X-Internal-Token` shared secret (defense in depth);
   MFA remains mandatory for human sessions only.
4. **Durable-ledger retries, not Celery retries.** Tasks run with
   `acks_late=True`, `worker_prefetch_multiplier=1`, time limits, and
   `max_retries=0`. A failure is persisted on the queue item with
   exponential backoff + jitter (or marked terminal); the admin dashboard
   can requeue terminal work. Late-ack redelivery re-executes a `claimed`
   item idempotently (executors are idempotent-safe).
5. **Single-scheduler Beat with DB-driven ticks.** Celery Beat only wakes
   a `automation.beat_tick` task; the tick acquires a Redis `SET NX EX`
   lock (`atoz:automation:beat:lock`) before scanning `scheduled_jobs`
   (`status=enabled`, `next_run_at <= now`), enqueues one execution per due
   job, and advances `next_run_at` with croniter (UTC). When Redis is
   unavailable the tick returns `locked`/`unavailable` safely — a missed
   tick never double-enqueues because `UNIQUE (niche_id, job_key)` and the
   queue-ledger dedupe protect the database.
6. **Notifications are best-effort, at-most-once.** After each execution
   outcome the workflow notifies through the admin internal channel once;
   delivery failures are logged and never fail the execution, and no
   infinite notification retry exists.

## Consequences

- **Positive:** scheduler, queue, executors, and notifications are all
  testable without a broker (in-memory buses, mocked sibling transports);
  Celery is a delivery transport only; tenancy is enforced end-to-end by
  the forwarding header + server-side scoping in every sibling service.
- **Negative:** service-to-service JWT secrets must be provisioned per
  sibling (Vault); the Beat lock requires Redis in production (falls back
  to safe-skip without it).
- **Future:** per-executor Celery queues (`task_routes`) and Temporal
  (if workflows outgrow Celery) can be layered on without changing the
  ledger contract.
