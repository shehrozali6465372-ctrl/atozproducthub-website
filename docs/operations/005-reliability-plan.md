# 005 — Reliability & Failure Injection (M11 Phase G)

- **Date:** 2026-08-14
- **Owner:** @atoz/platform, @atoz/lead

## 1. What is verified automatically (per push)

| Failure class | Coverage | Where |
|---|---|---|
| External API 429 | Retry + backoff, exhaustion, `retryable` flag | pinterest `test_client.py` (M6) |
| External API 403 | Non-retryable hard failure | pinterest `test_client.py` (M6) |
| External API 401 | Token refresh once, hard failure after refresh | pinterest `test_client.py` (M6) |
| External API 5xx | Retry + exhaustion (Phase G) | pinterest `test_client.py` |
| External API timeout | `httpx.ReadTimeout` retried, then success (Phase G) | pinterest `test_client.py` |
| Redis down | `/ready` returns 503 degraded (Phase G) | backend-core `test_readiness.py` |
| Duplicate execution / idempotency | Webhook/conversion idempotency, publish dedupe, late-ack redelivery | affiliate (M5), pinterest (M6), automation `test_workflow.py` (M10) |
| Queue recovery | Claim/complete/fail + retry-to-max, ledger rebuild | automation (M10) |
| Worker failure | Late-ack redelivery after crash | automation `test_celery.py` / `test_workflow.py` (M10) |
| Niche/account isolation | 10-account + cross-niche leakage tests | every milestone |
| DB migration failure | Fresh PostgreSQL upgrade/downgrade/re-upgrade per stream | CI `database` job |
| Backup/restore | backup → wipe → restore → verify | CI `recovery` job (Phase E) |
| Metrics loop failure | Degrades to warning, never crashes (Phase G) | automation `test_observability.py` |

## 2. Load / stress (staging, dev-only tooling)

- `tools/loadtest/` provides a Locust profile (reader + operator mix).
- Gates: p95 < 500 ms, error rate < 1% at target concurrency; run against
  staging with the SLO dashboard live.
- Never load-test external providers (Pinterest/affiliate/AI OS); publish
  paths are covered by queue reliability tests instead.

## 3. Production reliability validation (30-day window)

Tracked in [006-launch-audit.md](006-launch-audit.md) and measured from the
SLO dashboard:

- Availability of reader + API surfaces ≥ 99.9% (30-day window).
- p95 latency < 500 ms for public reads; publish freshness < 15 min.
- Zero missed scheduled runs (Beat single-scheduler lock verified).
- Zero queue items stuck > 2× retry budget; alert on starvation.
- Weekly restore drill + monthly full DR drill in staging.
- Chaos windows (staging): Redis restart, Postgres restart, worker kill,
  Kafka broker restart — each must recover without manual intervention.
