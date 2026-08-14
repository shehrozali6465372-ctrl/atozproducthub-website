# 006 — Final Launch Audit (M11 Phase H)

- **Date:** 2026-08-14
- **Owner:** @atoz/lead, @atoz/platform
- **Status:** Audit framework + evidence to date. Live gates (30-day
  reliability, Go/No-Go) are production-time checkpoints.

## 1. Security audit

| Item | Evidence | Status |
|---|---|---|
| Secrets out of code/build artifacts | `.gitignore`/`.dockerignore`, gitleaks CI job, prod compose `${VAR:?}` only | ✅ v0.12.0 |
| Dev credentials disabled in prod | backend-core prod secrets guard (rejects `dev-only-`/`dev-admin`/`CHANGE_ME`/empty secrets) | ✅ v0.13.0 |
| Store security (auth/TLS) | Redis `requirepass`, ClickHouse user/password, Kafka SASL_PLAINTEXT, Postgres password | ✅ v0.13.0 (TLS-at-rest/edge documented; full store TLS Phase C follow-up) |
| Vault integration | `atoz_backend_core.security.vault` client + rotation policy + Vault-sourced env contract | ✅ v0.13.0 boundary |
| Secret rotation | `infra/secrets/rotation.md` (cadence, dual-publish, incident rules) | ✅ v0.13.0 |
| Container hardening | Non-root, read-only root, resource limits, network isolation, TLS edge | ✅ v0.12.0 |
| Dependency audit | `pip-audit` in CI (green), no-AI guard, contract guard | ✅ per push |

## 2. Observability audit

| Item | Evidence | Status |
|---|---|---|
| Metrics | `/metrics` on every service + queue/job gauges | ✅ v0.13.0 |
| Dashboards | Grafana provisioning + ops dashboard (requests, error rate, queue, jobs) | ✅ v0.13.0 |
| Alerts | Prometheus SLO rules (ServiceDown, HighErrorRate, SlowP95, QueueStarvation, QueueFailureSpike, StuckRunningJobs) + Alertmanager | ✅ v0.13.0 |
| Centralized logs | Loki + Promtail (docker logs) | ✅ v0.13.0 |
| Traces | OTel collector + `OTEL_ENABLED` hooks | ✅ v0.13.0 (export pipeline Phase D follow-up) |

## 3. Backup / restore evidence

- CI `recovery` job: backup → wipe → restore → data-verified on every push
  (v0.13.0).
- RPO/RTO + runbook: `docs/operations/003-disaster-recovery.md`.
- Migration recovery: `database` job downgrade/re-upgrade per stream.

## 4. Deployment / rollback evidence

- `.github/workflows/deploy.yml` (staging/prod, migration gate, smoke,
  rollback step) — scaffolded; activation requires Phase F runner+secrets.
- Runbook: `docs/operations/004-deployment-and-rollback.md`.

## 5. Performance / SLO audit

- Local gates: full test suite, Lighthouse (perf/SEO) in CI.
- Staging gates (production-time): p95 < 500 ms, error rate < 1% at load,
  queue freshness < 15 min (Locust profile in `tools/loadtest/`).

## 6. 30-day reliability validation (production-time gate)

Run for 30 continuous days after production rollout, tracked on the SLO
dashboard and reviewed weekly:

- Availability ≥ 99.9% (reader + API surfaces).
- p95 < 500 ms; error rate < 1%; zero missed scheduled runs.
- Weekly restore drill; monthly full DR drill.
- No manual intervention required after injected failures (chaos windows).

## 7. Final Go / No-Go

| Gate | Criteria | Sign-off |
|---|---|---|
| Security audit | All items above closed (store TLS follow-up acknowledged) | @atoz/lead |
| Observability | Dashboards + alerts live and paging on-call | @atoz/platform |
| Backup/restore | Restore drill green in production too | @atoz/platform |
| Deployment | Staging green; prod rollout rehearsed; rollback exercised | @atoz/platform |
| 30-day reliability | SLOs met with zero SLO breaches | @atoz/lead |
| Website Contract | Business-layer-only confirmed; no AI duplication | @atoz/lead |

**Result:** pending production rollout + 30-day window. This document is
the audit checklist; each row is signed and dated as evidence accrues.
