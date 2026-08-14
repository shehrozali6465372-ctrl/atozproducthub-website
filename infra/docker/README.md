# docker

Docker files and Compose for local development and production.

## Local development (`compose.yml`)

```bash
docker compose -f infra/docker/compose.yml up -d --build
```

Runs the full business stack with dev secrets, host ports for convenience,
and liveness probes. Images are built hardened (non-root `appuser`) — the
CI docker job builds and smoke-tests this file.

## Production (`compose.prod.yml`)

The production profile applies M11 Phase B hardening (ADR-0012):

- Non-root, read-only root filesystem, tmpfs `/tmp`, bounded CPU/memory/pids.
- Trust-zone networks: `edge` (Caddy TLS), `app` (services), `data`
  (stores, internal), `integration` (AI OS Bridge egress).
- No host ports except the Caddy edge (80/443).
- Liveness (`/health`) + readiness (`/ready`) probes.
- Zero literal secrets: every credential is a `${VAR:?...}` interpolation
  injected by the deployment pipeline from the Vault.

```bash
# validate
docker compose -f infra/docker/compose.prod.yml config -q

# deploy (secrets injected by the pipeline / Vault)
docker compose -f infra/docker/compose.prod.yml up -d
```

Required variables are documented in `config/prod/env.template`; the
mapping is enforced by `tools/dev/check-infra.sh` in CI.

## TLS edge

`caddy/Caddyfile` terminates TLS (Let's Encrypt), applies security headers,
and routes `https://api.<domain>` to the gateway. The public site and admin
app remain CDN-first / application-track (Phase F wiring points commented).

## Hardening guard

```bash
bash tools/dev/check-infra.sh
```

Static checks (no Docker): non-root images, prod-compose hardening,
network isolation, no host ports on services/stores, no placeholder
tokens, documented variables, Caddyfile present.
