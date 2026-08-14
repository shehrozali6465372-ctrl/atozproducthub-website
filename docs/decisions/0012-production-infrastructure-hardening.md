# ADR-0012 — Production Infrastructure Hardening (M11 Phase B)

- **Status:** Accepted
- **Date:** 2026-08-14
- **Owner:** @atoz/platform, @atoz/lead
- **Documents affected:** 07-security-boundaries.md, 08-deployment-strategy.md, 10-technology-stack.md, 14-implementation-roadmap.md, CHANGELOG.md, docs/operations/001-production-audit.md, docs/operations/002-production-infrastructure.md

## Context

Task 22 (M11 Production Foundation) moves the business layer from
feature-complete to production-hardened. Phase A audited the v0.11.0 stack
and found: root containers, unbounded resources, host-port exposure for
every service, no network segmentation, no TLS edge, and dev-only secret
defaults that would silently boot in `prod`. Phase B must fix these without
changing business behavior and without introducing AI functionality.

## Decision

1. **Non-root images.** All 10 first-party images run as `USER appuser`
   (system user; writable state via volumes only, `/data/content` for the
   content store).

2. **Production compose profile.** `infra/docker/compose.prod.yml`:
   - read-only root filesystem + tmpfs `/tmp` for first-party services;
   - `mem_limit`/`cpus`/`pids_limit` (+ `deploy.resources` for
     orchestration parity);
   - trust-zone networks (`edge`, `app`, `data` internal, `integration`)
     with the Caddy edge as the only host ingress (80/443);
   - liveness `/health` and readiness `/ready` probes (readiness verifies
     Postgres/Redis);
   - zero literal secrets — every credential is `${VAR:?...}` fail-fast.

3. **Production secrets guard.** `BaseServiceSettings` rejects any string
   containing `dev-only-`, `dev-admin`, or `CHANGE_ME` when `APP_ENV=prod`
   (recursive through dict/list/tuple fields), so a dev default can never
   reach a live deployment.

4. **TLS edge.** Caddy 2 terminates TLS (Let's Encrypt), applies security
   headers (HSTS preload, CSP, nosniff, frame/referrer/permissions
   policies), strips `Server`, and routes only the API; the frontend track
   stays CDN-first (Phase F wiring points commented).

5. **CI enforcement.** `tools/dev/check-infra.sh` (quality job) statically
   verifies non-root images, prod-compose hardening, network isolation, no
   host ports on services/stores, no placeholder tokens, and documented
   interpolation variables. The docker job validates the prod profile with
   `docker compose config -q` and still runs the dev-compose smoke on the
   hardened images.

## Consequences

- Dev-compose behavior is unchanged for developers; images are now
  non-root everywhere (CI smoke verifies the health checks still pass).
- Production deploys fail fast on missing secrets or surviving dev
  defaults instead of booting insecure.
- The compose contract requires the deployment pipeline to inject ~24
  documented variables from the Vault (Phase C wires the Vault client).
- Services must not add runtime writes outside their volumes (read-only
  root); the guard enforces `read_only` in the prod profile.
- Remaining production work (Vault client, Redis/store auth, mTLS, OTel
  collector, dashboards/alerts, backups/DR, deployment workflows) is
  tracked in Phases C–F and the implementation roadmap.

## Contract compliance

- Website remains a business platform only; no AI logic, no AI SDKs, no
  duplicated AI OS functionality (Website Contract §4).
- AI OS contact remains exclusively `services/aios-bridge`; the prod
  profile routes the bridge on `app` + `integration` networks only.
- Tenancy model unchanged: `niche_id`/`pinterest_account_id` scoping is
  untouched by infrastructure hardening.
