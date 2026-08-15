# staging

Staging environment configuration (Task 24 / M11 Phase 3, ADR-0014).

- `env.template` documents every non-secret value the staging stack needs;
  secrets are marked `Vault` and are injected by the deployment pipeline —
  never committed.
- `infra/docker/compose.staging.yml` is the compose overlay applied on top
  of `compose.prod.yml`; it changes only environment identity (`APP_ENV`,
  domains, CORS) and reuses every production hardening rule.
- `tools/dev/check-staging.sh` validates the staging profile in CI:
  required services present, no host ports, no literal credentials, and all
  required interpolation variables documented.

Validate locally (no side effects):

```bash
export $(grep -v '^#' config/staging/env.template | xargs)
docker compose -f infra/docker/compose.prod.yml -f infra/docker/compose.staging.yml config -q
```
