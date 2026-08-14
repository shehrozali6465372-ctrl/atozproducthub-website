# 001 — Production Audit (M11 Phase A)

- **Date:** 2026-08-14
- **Owner:** @atoz/platform, @atoz/lead
- **Scope:** Phase A of M11 Production Foundation — a point-in-time audit of
  the repository state at v0.11.0 against the production requirements in
  [08-deployment-strategy.md](../architecture/08-deployment-strategy.md) and
  [07-security-boundaries.md](../architecture/07-security-boundaries.md).
- **Companion:** [002-production-infrastructure.md](002-production-infrastructure.md)
  records the Phase B hardening implemented as a result of this audit.

## 1. Findings summary

| # | Area | Finding | Severity | Status |
|---|------|---------|----------|--------|
| A1 | Docker/Compose | Containers run as `root`; no resource limits; every service publishes a host port; no network isolation | High | Fixed in Phase B |
| A2 | Environment/config | Dev defaults (`dev-only-*`) are the compiled-in values; production must fail fast if they survive | High | Fixed in Phase B (backend-core prod secrets guard) |
| A3 | Secrets | Compose hardcodes dev secrets; `.env`/Vault references exist but no enforcement | High | Partially fixed (guard + no secrets in prod compose); Vault integration is Phase C |
| A4 | Auth/RBAC/MFA | RBAC + MFA gates exist (M9); dev auth endpoint already returns 501 in prod | Low | Passed; Phase C reviews session hardening |
| A5 | Inter-service security | Service-to-service JWT exists (ADR-0011); prod compose now enforces separate per-service secrets | Medium | Fixed in Phase B (env contract); mTLS is a documented Phase C follow-up |
| A6 | Stores | Postgres/Redis/Kafka/ClickHouse/Typesense exposed to the host in dev; no auth on Redis; no host exposure in prod profile | High | Fixed in Phase B (internal `data` network); Redis auth is Phase C |
| A7 | Health/readiness | `/health`, `/ready`, `/metrics` exist; dev compose probes only liveness; prod profile probes `/ready` (verifies Postgres/Redis) | Medium | Fixed in Phase B |
| A8 | TLS/edge | No TLS termination or reverse-proxy boundary in the container stack | High | Fixed in Phase B (Caddy edge) |
| A9 | Observability | Metrics/OTel hooks exist but no collector, dashboards, or alerts | Medium | Phase D (not in this milestone) |
| A10 | Backup/DR | No backup tooling, retention policy, or restore drills | High | Phase E (not in this milestone) |
| A11 | Deployment | No staging/production workflow, migration gate, or rollback automation | High | Phase F (not in this milestone) |

## 2. Audit detail

### 2.1 Docker/Compose (A1)

Observed at v0.11.0:

- All 10 images (`infra/docker/api.Dockerfile` + `services/*/Dockerfile`)
  run the default user (`root`).
- `infra/docker/compose.yml` publishes host ports for every service
  (8000–8800) and for Postgres, Redis, Typesense, Kafka, and ClickHouse.
- No `mem_limit`/`cpus`/`pids_limit` or `deploy.resources` limits.
- No network segmentation; every container shares the default network.
- Healthchecks exist on API services (liveness only); Celery worker/Beat
  have none (they expose no HTTP).

Remediation (Phase B): non-root `USER appuser`, bounded resources,
read-only root + tmpfs, trust-zone networks, proxy-only ingress,
readiness probes — see 002.

### 2.2 Environment/config (A2)

Every service `Settings` class compiles dev-only defaults
(`dev-only-*-change-in-production`, `dev-admin`, placeholder hashes).
`config/prod/env.template` documents Vault sourcing but nothing prevented a
service from booting in `prod` with a default.

Remediation (Phase B): `BaseServiceSettings` now rejects any string
containing `dev-only-`, `dev-admin`, or `CHANGE_ME` when `APP_ENV=prod`
(validated recursively through dict/list/tuple fields). Startup fails fast;
CI tests cover the guard. `config/prod/env.template` now documents every
required interpolation variable and the infra guard enforces the mapping.

### 2.3 Secrets (A3)

- Dev compose carries explicit dev secrets (expected for local dev).
- Production compose previously did not exist.
- `.env` is git-ignored; `.dockerignore` excludes `.env` and key material.
- Vault is referenced by path (`vault://...`) in service configs but no
  vault client is wired.

Phase B: production compose contains zero literal secrets — every
credential is a `${VAR:?...}` interpolation that fails fast when missing,
and the infra guard rejects `dev-only-`/`CHANGE_ME` literals in the prod
compose. Vault client integration, rotation policy, and audit of secret
reads remain Phase C.

### 2.4 Auth/RBAC/MFA (A4)

- Admin RBAC matrix, permission catalog, MFA gate, and revocable sessions
  (M9) are in place and tested.
- Gateway dev-auth endpoint hard-returns 501 when `APP_ENV=prod`.
- Phase C will re-audit session TTLs, refresh rotation, and brute-force
  protection.

### 2.5 Inter-service security (A5)

- Automation executors mint short-lived service JWTs (ADR-0011).
- Dev compose shares one implicit secret family; prod compose now requires
  a distinct JWT secret per service and injects sibling secrets explicitly.
- Phase C follow-ups: mTLS or network policy at the container level, and
  per-service Vault identities.

### 2.6 Stores (A6)

- Dev compose exposes Postgres (5432), Redis (6379), Typesense (8108),
  Kafka (9092), ClickHouse (8123/9000) to the host.
- Redis has no authentication (dev); Typesense uses a dev API key.
- Phase B: the prod profile places all stores on an `internal` network with
  no host ports; only the TLS edge is reachable. Redis `requirepass` and
  store-level TLS are Phase C items.

### 2.7 Health/readiness (A7)

- backend-core ships `/health` (liveness), `/ready` (checks Postgres/Redis),
  `/metrics` (Prometheus).
- Phase B: prod profile liveness + readiness probes on every API service
  and `start_period` for dependency warm-up.

### 2.8 TLS/edge (A8)

- No TLS termination existed in the container stack (CDN is the documented
  edge for content; the application track had no edge).
- Phase B: Caddy 2 edge terminates TLS (Let's Encrypt), applies security
  headers (HSTS preload, CSP, nosniff, frame/ referrer/ permissions
  policies), and routes only the API; the frontend track remains CDN-first.

### 2.9–2.11 Remaining phases

- **Phase C — Secrets & security:** Vault client, rotation policy,
  store-level auth/TLS, mTLS, security-header review of frontends.
- **Phase D — Observability:** collector, dashboards, alerts, queue-depth
  and security-event monitoring.
- **Phase E — Backup + DR:** Postgres/object-store backups, retention,
  restore drills, RPO/RTO runbook.
- **Phase F — Deployment:** staging/production workflow, migration gate,
  smoke tests, rollback, release audit trail.

## 3. Compliance mapping

| Requirement (Task 22 Phase B) | Where satisfied |
|---|---|
| Production Compose/deployment profile | `infra/docker/compose.prod.yml` |
| Resource limits | `mem_limit`, `cpus`, `pids_limit` + `deploy.resources` |
| Non-root containers | `USER appuser` in all 10 images; guarded in CI |
| Read-only filesystem | `read_only: true` + tmpfs `/tmp` (first-party services) |
| Health/readiness/startup probes | `/health` + `/ready` probes with `start_period` |
| TLS/reverse-proxy boundary | Caddy 2 edge (`infra/docker/caddy/Caddyfile`) |
| Network isolation | `edge`/`app`/`data`(internal)/`integration` networks |
| Production credentials disabled by default | backend-core prod secrets guard + `${VAR:?}` compose contract |
| CI verification | `check-infra.sh` (quality) + `docker compose config -q` (docker job) |
