# 002 — Production Infrastructure (M11 Phase B)

- **Date:** 2026-08-14
- **Owner:** @atoz/platform
- **ADR:** [0012 — Production Infrastructure Hardening](../decisions/0012-production-infrastructure-hardening.md)
- **Audit:** [001 — Production Audit](001-production-audit.md)

This document describes the production deployment profile implemented in
M11 Phase B. It complements (and does not replace) the frozen planning
documents — [08-deployment-strategy.md](../architecture/08-deployment-strategy.md)
and [07-security-boundaries.md](../architecture/07-security-boundaries.md).

## 1. Artifacts

| Artifact | Purpose |
|----------|---------|
| `infra/docker/compose.prod.yml` | Production profile: hardened services, stores, edge, networks |
| `infra/docker/compose.staging.yml` | Staging overlay (M11 Phase 3 / ADR-0014): identity-only override on the prod profile |
| `infra/docker/caddy/Caddyfile` | TLS termination + security headers (Caddy 2) |
| `tools/dev/check-infra.sh` | Static hardening guard (runs in CI quality job, no Docker) |
| `tools/dev/check-staging.sh` | Staging overlay guard (services, APP_ENV, ports, secrets, template vars) |
| `config/prod/env.template` | Documented production variables (secrets via Vault) |
| `config/staging/env.template` | Documented staging variables (secrets via Vault) |
| Dockerfiles (`USER appuser`) | Non-root runtime images for all first-party services |

## 2. Trust-zone networking

Mapping to [07-security-boundaries.md](../architecture/07-security-boundaries.md):

| Compose network | Zone | Members | Exposure |
|-----------------|------|---------|----------|
| `edge` | Z2 edge | `proxy` only | Host 80/443 (TLS) |
| `app` | Z4/Z6 | All first-party services + `proxy` | Internal only |
| `data` | Z7 | Postgres, Redis, Typesense, Kafka, ClickHouse | `internal: true` — no outbound, no host ports |
| `integration` | Z8 | `aios-bridge` (egress to the AI OS) | Internal only |

First-party services join `app` + `data` (service ↔ service over `app`;
service ↔ store over `data`). Stores join only `data`. `proxy` joins
`edge` + `app`. No store and no service publishes a host port in the prod
profile — the Caddy edge is the only ingress.

## 3. Container hardening

- **Non-root:** every image ends with `USER appuser` (system user, no
  password, home-less). Content bodies remain writable through the
  `content_data` volume (image pre-creates `/data/content` owned by
  `appuser`).
- **Read-only root:** first-party services run `read_only: true` with a
  tmpfs `/tmp`. Bytecode writes are disabled (`PYTHONDONTWRITEBYTECODE=1`).
- **Resource limits:** `mem_limit` + `mem_reservation`, `cpus`,
  `pids_limit`, and `deploy.resources.limits/reservations` for
  orchestration parity. Stores get larger budgets (Postgres/Kafka/
  ClickHouse 1 GB, Typesense 512 MB, Redis 256 MB).
- **Restart policy:** `restart: unless-stopped`.

## 4. Probes

- Compose healthchecks hit `GET /ready`, which verifies Postgres and Redis
  — dependencies are actually checked before a container is considered
  healthy (per Task 22 Phase B). `GET /health` remains the liveness
  endpoint for orchestrators.
- `start_period` accommodates migration/startup warm-up; Celery
  worker/Beat run without HTTP probes (no port) and are covered by queue
  monitoring in Phase D.

## 5. TLS edge

Caddy 2 terminates TLS (automatic Let's Encrypt via
`infra/docker/caddy/Caddyfile`), applies HSTS (preload), CSP, nosniff,
frame/referrer/permissions policies, gzip/zstd encoding, and strips the
`Server` header. `https://api.<domain>` proxies the gateway;
`/healthz` returns 204 for load-balancer checks. The public site and admin
app remain CDN-first / application-track (Phase F wiring points are
commented in the Caddyfile).

## 6. Production secrets contract

- `compose.prod.yml` contains **zero literal credentials**. Every secret is
  `${VAR:?...}` and fails `docker compose config` when unset.
- `config/prod/env.template` documents every required variable; the infra
  guard enforces that no `${VAR:?...}` is undocumented.
- The backend-core **production secrets guard** rejects any string
  containing `dev-only-`, `dev-admin`, or `CHANGE_ME` at startup when
  `APP_ENV=prod` — dev defaults cannot silently reach production.
- Vault client integration and rotation policy are Phase C.

## 7. Deployment commands

```bash
# validate (no side effects)
export $(grep -v '^#' config/prod/env.template | xargs)   # non-secret defaults
docker compose -f infra/docker/compose.prod.yml config -q

# deploy (secrets injected by the pipeline / Vault)
docker compose -f infra/docker/compose.prod.yml up -d
```

## 8. Staging profile (M11 Phase 3, ADR-0014)

Staging runs the **same** hardened profile with a thin identity overlay:

```bash
docker compose -f infra/docker/compose.prod.yml -f infra/docker/compose.staging.yml \
  --env-file config/staging/env.template up -d
```

The overlay only sets the project name, `APP_ENV=staging`, staging domains,
CORS, and the OAuth redirect URI. Every hardening rule (edge-only ingress,
internal data network, non-root read-only containers, resource limits,
`${VAR:?}` secrets) is inherited from the production profile — verified by
`tools/dev/check-staging.sh` in CI and by the staging pytest suite.

## 8. Out of scope (later phases)

- Phase C — Vault integration, Redis/store auth, mTLS, rotation.
- Phase D — OTel collector, dashboards, alerts, queue-depth monitoring.
- Phase E — backups, retention, restore drills, RPO/RTO runbook.
- Phase F — staging/production workflows, migration gate, rollback,
  frontend containers.
