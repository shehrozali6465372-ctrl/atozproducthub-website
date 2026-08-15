# 007 — Staging Validation & Production Blockers (M11 Phase 3)

- **Date:** 2026-08-15
- **Owner:** @atoz/platform, @atoz/lead
- **ADR:** [0014 — Staging Deployment & Production Validation](../decisions/0014-staging-validation.md)
- **Release:** v0.14.0 (Task 24)

## 1. Summary

This phase builds every staging validation capability that can be
implemented and verified in code: a production-like staging compose
profile, a fail-closed deployment pipeline, consolidated database
validation, a 24-item smoke suite, failure/recovery drills, load-test
baselines, observability checks, backup/restore and rollback automation,
and security validation. No real production deployment was performed
and no external credentials were invented; the live-staging and
production gates are listed as blockers with exact next actions.

## 2. Completed checks (with automated evidence)

| Phase | Check | Evidence |
|---|---|---|
| A | Staging compose overlay + env template | `infra/docker/compose.staging.yml`, `config/staging/env.template`, `tools/dev/check-staging.sh` (CI quality + staging jobs) |
| A | All 23 required services represented | `tests/staging/test_staging_config.py::test_all_required_services_present` |
| A | No host ports, no literal credentials, APP_ENV=staging | `tests/staging/test_staging_config.py` |
| B | Pre-deploy validation (lint, mypy, guards, pip-audit, npm audit) | `.github/workflows/deploy.yml` `validate` job |
| B | Immutable GHCR SHA tags + image override | `tools/deploy/write-image-override.sh`; `build-push` job |
| B | Migration gate before rollout (all 7 streams) | `tools/deploy/run-migration-gate.sh` |
| B | Fail-closed readiness + smoke | `tools/deploy/staging-smoke.sh` (edge + `DOCKER=1` container health) |
| B | Previous release preserved; rollback step | `.last-deployed-tag` on host + `Rollback on failure` |
| B | Production manual/approval-gated only | `environment: prod` + GitHub protection rule (documented, enforced by GitHub) |
| C | Single head per stream, distinct version tables | `tools/db/validate-migrations.sh` (CI `staging` job) |
| C | Upgrade, schema smoke, downgrade + re-upgrade | `tools/db/validate-migrations.sh validate` |
| C | Tenancy `niche_id` columns + unique/idempotency constraints | `tools/db/validate-migrations.sh` SQL assertions |
| D | 24-item smoke matrix (unit level, mocks) | `tests/staging/test_staging_smoke.py` (57 staging tests total) |
| D | Live smoke script (edge + containers) | `tools/deploy/staging-smoke.sh` |
| E | Redis/Postgres down -> degraded readiness | `tests/staging/test_failure_recovery.py` |
| E | Kafka/ClickHouse/Typesense down -> retryable failures + fallback | `tests/staging/test_failure_recovery.py` |
| E | Pinterest 429/5xx/timeout -> retry -> recovery | `tests/staging/test_failure_recovery.py` |
| E | Duplicate webhook/queue -> ledger unique constraints | `tests/staging/test_failure_recovery.py` |
| E | Retry exhaustion + recovery scheduling | `tests/staging/test_failure_recovery.py` |
| F | Load-test scenarios + frozen thresholds | `tools/loadtest/baselines.yml`, `tools/loadtest/locustfile.py`, `tests/staging/test_load_baselines.py` |
| G | Prometheus targets, SLO alerts, metrics names, Grafana, Loki, OTel | `tools/observability/check-observability.sh`, `tests/staging/test_observability_checks.py` |
| G | Request-ID log correlation; no raw settings/credentials in logs | `tests/staging/test_observability_checks.py` |
| H | Backup -> destroy -> restore -> verify + idempotency + migrations + readiness + RPO/RTO evidence | `tools/db/staging-recovery-drill.sh`; CI `recovery` job per push |
| I | Deploy N -> N+1 -> controlled failure -> rollback N -> health/DB/queue checks | `tools/deploy/rollback-test.sh`, `tests/staging/test_rollback_plan.py` |
| J | pip-audit, npm audit, ruff, mypy, frontend typecheck/lint/tests/build, no-AI, contracts, infra, staging, observability guards, gitleaks, secret scan, Docker validation | CI `quality`/`security`/`staging`/`docker` jobs + `tools/dev/check-security.sh` |

## 3. Failed checks

- None. All checks that could run in this environment are green (see
  release evidence in `docs/operations/006-launch-audit.md`).

## 4. Skipped checks (blocked on external infrastructure)

| Check | Blocker | Required input |
|---|---|---|
| Real staging stack deploy | No self-hosted runner/host | Runner tagged `deploy` with Docker Compose + checkout at `/opt/atozproducthub` |
| Live staging smoke | No deployed staging DNS | `DEPLOY_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_ENV_FILE` |
| Live restore drill + RTO actuals | No staging Postgres | Staging database credentials in Vault |
| Live rollback drill | No staging host | Same runner/SSH credentials as deploy |
| Load-test results | No staging stack | Staging deployment + DNS |
| OTel export pipeline | No trace backend endpoint | Production trace backend URL in Vault |
| Pinterest OAuth live flow | Pinterest app credentials | `PINTEREST_OAUTH_CLIENT_ID`/secret in Vault |
| Google/Bing live integration | Google/Bing credentials | Search Console / Bing Webmaster keys in Vault |
| 30-day reliability validation | Requires production rollout | See `006-launch-audit.md` |

## 5. External blockers (exact next actions)

1. **Infrastructure:** provision the `deploy` self-hosted runner (Docker
   Compose + repo checkout at `/opt/atozproducthub`).
2. **Credentials:** create repository secrets `DEPLOY_HOST`,
   `DEPLOY_SSH_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_ENV_FILE` (base64
   `.env.staging` for staging, `.env.prod` for production).
3. **DNS:** point `staging.atozproducthub.dev`, `api.staging.atozproducthub.dev`,
   `admin.staging.atozproducthub.dev` at the staging host (Caddy issues TLS).
4. **Vault:** populate every `CHANGE_ME` value from `config/staging/env.template`
   and `config/prod/env.template` (rotation policy: `infra/secrets/rotation.md`).
5. **Approvals:** add the GitHub environment protection rule for `prod`
   (required reviewers) — the workflow never auto-deploys production.
6. **Deploy:** run the workflow manually with `environment: staging`, then
   `run_rollback_test: true` once, then repeat for `environment: prod` after
   the staging gate passes.

## 6. Exact commands / workflows

```bash
# validate everything locally (no Docker)
bash tools/dev/check-staging.sh
bash tools/observability/check-observability.sh
bash tools/dev/check-security.sh
bash tools/db/validate-migrations.sh validate   # needs PostgreSQL + DATABASE_URL

# live staging drills (on the deploy host)
STAGING_BASE_URL=https://api.staging.atozproducthub.dev DOCKER=1 \
  bash tools/deploy/staging-smoke.sh
PREV_TAG=<sha> NEXT_TAG=<sha> ENV_FILE=/opt/atozproducthub/.env.staging \
  bash tools/deploy/rollback-test.sh
PGPASSWORD=<...> RUN_MIGRATIONS=1 \
  STAGING_BASE_URL=https://api.staging.atozproducthub.dev \
  bash tools/db/staging-recovery-drill.sh

# deploy
# GitHub Actions -> Deploy -> environment: staging (then prod, with approval)
```

## 7. Go / No-Go prerequisites

The final Go decision requires all of the following (see
`006-launch-audit.md` for sign-off owners):

- [ ] Staging stack deployed and `staging-smoke.sh` green (Phase A/B).
- [ ] Staging restore drill green with RTO actual < 4 h (Phase H).
- [ ] Staging rollback drill green (Phase I).
- [ ] Load test at target concurrency meets `baselines.yml` thresholds (Phase F).
- [ ] 30-day reliability window met with zero SLO breaches (Phase G/H).
- [ ] Security audit closed; Website Contract ratified (Phase J/H).
- [ ] Production rollout executed only after explicit human approval.

**Status: STAGING READY — PRODUCTION BLOCKED on the external blockers above.**
