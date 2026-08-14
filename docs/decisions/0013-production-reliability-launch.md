# ADR-0013 — Production Reliability & Launch (M11 Phase 2)

- **Status:** Accepted
- **Date:** 2026-08-14
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 07-security-boundaries.md, 08-deployment-strategy.md, 10-technology-stack.md, 14-implementation-roadmap.md, CHANGELOG.md, docs/operations/001–006

## Context

Task 23 (M11 Phase 2) hardens the v0.12.0 stack for launch: secrets and
store security (C), observability and alerts (D), backup and disaster
recovery with a tested restore (E), deployment and rollback (F), reliability
and failure injection (G), and the final launch audit (H). The website must
stay a business platform; every reliability and security mechanism must be
verifiable in CI.

## Decision

1. **Secrets & data security (C).** backend-core rejects empty secret
   values in `prod` (in addition to dev-only tokens). Redis runs
   `requirepass`, ClickHouse gets user/password, Kafka moves to
   SASL_PLAINTEXT with per-broker credentials, and a guarded
   `VaultSecretsClient` (`vault://path?key=field` resolution, no-op when
   unconfigured) provides the Vault integration boundary. Rotation policy
   is documented in `infra/secrets/rotation.md` with a dual-publish window.

2. **Observability (D).** The prod profile adds otel-collector, Prometheus,
   Alertmanager, Grafana, Loki, and Promtail with configs as code under
   `infra/observability/`. SLO alert rules (ServiceDown, HighErrorRate,
   SlowP95Latency, QueueStarvation, QueueFailureSpike, StuckRunningJobs)
   encode the error-rate/latency/queue gates. automation-service exposes
   queue ledger and job-run gauges on `/metrics` (background refresh that
   degrades to a warning, never a crash).

3. **Backup & DR (E).** `infra/db/backup.sh` (custom-format `pg_dump`,
   retention, optional S3-compatible upload) and `infra/db/restore.sh`
   (`pg_restore --clean --if-exists`). A new CI `recovery` job runs the
   full drill — seed, backup, wipe, restore, verify — on every push.
   RPO/RTO and the runbook live in `docs/operations/003-disaster-recovery.md`.

4. **Deployment & rollback (F).** `.github/workflows/deploy.yml` builds and
   pushes GHCR images, runs the migration gate (`alembic upgrade head`)
   before rollout, smoke-tests `/healthz` + `/ready`, and rolls back to the
   previous image tag on failure. Manual dispatch only; activation requires
   the Phase F self-hosted runner and secrets.

5. **Reliability (G).** Failure-injection tests added for external 5xx and
   timeout retries (Pinterest client), Redis-down readiness (503 degraded),
   and metrics-loop resilience; idempotency/queue-recovery coverage from
   M5/M6/M10 remains green. Load tooling (`tools/loadtest/`) is dev-only.

6. **Launch audit (H).** `docs/operations/006-launch-audit.md` is the
   evidence checklist; the 30-day reliability validation and the final
   Go/No-Go are production-time gates defined with concrete criteria.

## Consequences

- Production requires more injected secrets (Redis/ClickHouse/Kafka +
  per-service JWT) — all documented in `config/prod/env.template` and
  enforced by the infra guard.
- The observability stack adds six containers to the prod profile (bounded
  memory; only Prometheus/Grafana/Loki keep state).
- Store auth means deploy scripts must provide credentials; rotation uses
  the documented dual-publish window to avoid signature mismatches.
- The deploy workflow is scaffolded, not active: it runs only on manual
  dispatch and fails fast until the runner + secrets are provisioned.
- 30-day reliability and Go/No-Go cannot be completed in the sandbox; they
  are defined as measurable gates with owners and evidence paths.

## Contract compliance

- Business layer only: metrics, backups, and deployment never invoke AI;
  AI OS contact remains exclusively `services/aios-bridge`.
- Tenancy unchanged: observability aggregates globally for alerting while
  the admin API keeps per-niche/account enforcement.
- No AI SDKs, no vector/embedding/LLM dependencies (no-AI guard green).
