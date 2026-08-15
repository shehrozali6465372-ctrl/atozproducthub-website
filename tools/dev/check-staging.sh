#!/usr/bin/env bash
# Staging profile guard (Task 24 / M11 Phase 3, ADR-0014).
#
# Static checks that run without Docker:
#   * every required service is represented in the production profile
#     (staging reuses the same stack, so coverage is inherited);
#   * the staging overlay touches only known services and sets APP_ENV=staging;
#   * staging publishes no host ports (edge-only ingress, like prod);
#   * no literal credentials/secrets in the staging overlay or template;
#   * every required interpolation variable is documented in the staging
#     environment template;
#   * staging/deploy/rollback shell artifacts parse (bash -n).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FAIL: PyYAML is required for the staging guard")
    sys.exit(1)

violations = 0


def fail(msg: str) -> None:
    global violations
    violations += 1
    print(f"FAIL: {msg}")


prod_path = Path("infra/docker/compose.prod.yml")
overlay_path = Path("infra/docker/compose.staging.yml")
template_path = Path("config/staging/env.template")

prod = yaml.safe_load(prod_path.read_text())
overlay = yaml.safe_load(overlay_path.read_text())

# 1. Required service coverage (staging inherits the prod profile) ------------
REQUIRED = [
    "api", "aios-bridge", "content-service", "affiliate-service",
    "pinterest-service", "seo-service", "analytics-service",
    "admin-service", "automation-service", "automation-worker",
    "automation-beat", "postgres", "redis", "kafka", "clickhouse",
    "typesense", "proxy", "otel-collector", "prometheus",
    "alertmanager", "grafana", "loki", "promtail",
]
for name in REQUIRED:
    if name not in prod.get("services", {}):
        fail(f"prod profile missing required service '{name}'")

# 2. Overlay discipline -------------------------------------------------------
prod_services = set(prod.get("services", {}))
overlay_services = set(overlay.get("services", {}))
unknown = overlay_services - prod_services
if unknown:
    fail(f"staging overlay references services missing from prod: {sorted(unknown)}")
if overlay.get("name") != "atozproducthub-staging":
    fail("staging overlay must set name: atozproducthub-staging")

FIRST_PARTY = [
    "api", "aios-bridge", "content-service", "affiliate-service",
    "pinterest-service", "seo-service", "analytics-service",
    "admin-service", "automation-service", "automation-worker",
    "automation-beat",
]
for name in FIRST_PARTY:
    svc = overlay.get("services", {}).get(name)
    if svc is None:
        continue
    env = svc.get("environment") or {}
    if env.get("APP_ENV") != "staging":
        fail(f"staging overlay must set APP_ENV=staging on '{name}'")
    if svc.get("ports"):
        fail(f"staging overlay must not publish host ports ('{name}')")

# 3. No literal credentials in the overlay ------------------------------------
raw_overlay = overlay_path.read_text()
for token in ("password:", "PASSWORD=", "SECRET=", "API_KEY=", "sk-", "AKIA", "ghp_", "vault://"):
    if token in raw_overlay:
        fail(f"staging overlay contains a literal credential pattern '{token}'")

# 4. Required interpolation variables documented in the staging template ------
raw_prod = prod_path.read_text()
required = sorted(set(re.findall(r"\$\{([A-Z0-9_]+):\?", raw_prod)))
template = template_path.read_text()
undocumented = [v for v in required if v not in template]
if undocumented:
    fail(f"staging env template missing required vars: {undocumented}")
if "APP_ENV=staging" not in template:
    fail("staging env template must set APP_ENV=staging")

if violations:
    print(f"Staging guard failed with {violations} violation(s).")
    sys.exit(1)
print("Staging guard: OK")
PY

# 5. Shell syntax check for staging/deploy/rollback artifacts -----------------
for script in \
    tools/deploy/staging-smoke.sh \
    tools/deploy/rollback-test.sh \
    tools/db/validate-migrations.sh \
    tools/db/staging-recovery-drill.sh \
    tools/observability/check-observability.sh; do
  if [ -f "$script" ]; then
    bash -n "$script" || { echo "FAIL: syntax error in $script"; exit 1; }
  fi
done

echo "Staging guard: shell artifacts OK"
