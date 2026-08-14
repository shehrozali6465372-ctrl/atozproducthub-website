#!/usr/bin/env bash
# Infrastructure hardening guard (M11 Phase B / ADR-0012).
# Static checks that run without Docker: non-root images, production
# compose hardening (read-only root, resource limits, network isolation,
# no host port exposure, no hardcoded secrets), required interpolation
# variables documented, and the TLS edge present.
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
    print("FAIL: PyYAML is required for the infra guard")
    sys.exit(1)

violations = 0
FIRST_PARTY = [
    "api", "aios-bridge", "content-service", "affiliate-service",
    "pinterest-service", "seo-service", "analytics-service",
    "admin-service", "automation-service", "automation-worker",
    "automation-beat",
]
STORES = ["postgres", "redis", "typesense", "kafka", "clickhouse"]
REQUIRED_NETWORKS = {"edge", "app", "data", "integration"}


def fail(msg: str) -> None:
    global violations
    violations += 1
    print(f"FAIL: {msg}")


# 1. Non-root Dockerfiles ----------------------------------------------------
dockerfiles = [Path("infra/docker/api.Dockerfile"), *sorted(Path("services").glob("*/Dockerfile"))]
for df in dockerfiles:
    text = df.read_text()
    if "USER appuser" not in text:
        fail(f"{df} does not run as a non-root user (USER appuser)")
    if "USER root" in text:
        fail(f"{df} explicitly switches to root")

# 2. Compose files parse ------------------------------------------------------
dev = yaml.safe_load(Path("infra/docker/compose.yml").read_text())
prod = yaml.safe_load(Path("infra/docker/compose.prod.yml").read_text())
if not isinstance(dev, dict) or not isinstance(prod, dict):
    fail("compose files did not parse as mappings")

# 3. Production compose hardening ---------------------------------------------
networks = set(prod.get("networks", {}))
missing = REQUIRED_NETWORKS - networks
if missing:
    fail(f"prod compose missing networks: {sorted(missing)}")
if not prod.get("networks", {}).get("data", {}).get("internal"):
    fail("prod 'data' network must be internal: true")

proxy = prod.get("services", {}).get("proxy")
if proxy is None:
    fail("prod compose has no 'proxy' (TLS edge) service")
else:
    ports = proxy.get("ports") or []
    if not any(str(p).startswith("80:") or str(p).startswith("443:") for p in ports):
        fail("prod proxy must publish ports 80 and 443")
    if "app" not in proxy.get("networks", []):
        fail("prod proxy must attach to the app network")
    if "edge" not in proxy.get("networks", []):
        fail("prod proxy must attach to the edge network")

for name, svc in prod.get("services", {}).items():
    if name in FIRST_PARTY:
        if not svc.get("read_only"):
            fail(f"prod service '{name}' must set read_only: true")
        if not svc.get("mem_limit"):
            fail(f"prod service '{name}' must set mem_limit")
        if not svc.get("cpus"):
            fail(f"prod service '{name}' must set cpus")
        if not svc.get("pids_limit"):
            fail(f"prod service '{name}' must set pids_limit")
        if svc.get("ports"):
            fail(f"prod service '{name}' must not publish host ports (proxy only)")
        if "app" not in (svc.get("networks") or []):
            fail(f"prod service '{name}' must attach to the app network")
    elif name in STORES:
        if svc.get("ports"):
            fail(f"prod store '{name}' must not publish host ports")
        extra = set(svc.get("networks") or []) - {"data"}
        if extra:
            fail(f"prod store '{name}' must attach only to the data network (got {sorted(extra)})")

raw_prod = Path("infra/docker/compose.prod.yml").read_text()
for token in ("dev-only-", "CHANGE_ME"):
    if token in raw_prod:
        fail(f"prod compose contains hardcoded placeholder token '{token}'")

# 4. Required interpolation variables are documented ---------------------------
template = Path("config/prod/env.template").read_text()
required = sorted(set(re.findall(r"\$\{([A-Z0-9_]+):\?", raw_prod)))
undocumented = [v for v in required if v not in template]
if undocumented:
    fail(f"prod compose required vars missing from config/prod/env.template: {undocumented}")

# 5. TLS edge exists -----------------------------------------------------------
if not Path("infra/docker/caddy/Caddyfile").exists():
    fail("infra/docker/caddy/Caddyfile is missing")

if violations:
    print(f"Infrastructure guard failed with {violations} violation(s).")
    sys.exit(1)
print("Infrastructure guard: OK")
PY
