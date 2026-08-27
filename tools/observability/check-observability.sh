#!/usr/bin/env bash
# Observability verification guard (Task 24 / M11 Phase 3, ADR-0014).
#
# Static checks that run without the stack:
#   * Prometheus scrapes every first-party service and alerts to Alertmanager
#   * every SLO alert rule exists (service-down, error rate, p95, queue)
#   * alert expressions reference metrics that actually exist in code
#   * Grafana provisioning loads (Prometheus + Loki datasources, dashboard)
#   * Loki receives structured logs via Promtail (docker socket, read-only)
#   * OTel collector accepts OTLP and has a traces pipeline
#   * request IDs are correlated into structured logs
#   * log format never dumps raw settings/credentials
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FAIL: PyYAML is required for the observability guard")
    sys.exit(1)

violations = 0


def fail(msg: str) -> None:
    global violations
    violations += 1
    print(f"FAIL: {msg}")


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except Exception as exc:  # noqa: BLE001
        fail(f"invalid YAML {path}: {exc}")
        return None


obs = Path("infra/observability")

# 1. Prometheus scrapes + alerting --------------------------------------------
prom = load_yaml(obs / "prometheus.yml")
if prom:
    targets = []
    for job in prom.get("scrape_configs", []):
        for cfg in job.get("static_configs", []):
            targets.extend(cfg.get("targets", []))
    for service in (
        "api", "aios-bridge", "content-service", "affiliate-service",
        "pinterest-service", "seo-service", "analytics-service",
        "admin-service", "automation-service",
    ):
        if not any(str(t).startswith(service + ":") for t in targets):
            fail(f"prometheus scrape config missing target for '{service}'")
    alert_targets = [
        t
        for am in prom.get("alerting", {}).get("alertmanagers", [])
        for cfg in am.get("static_configs", [])
        for t in cfg.get("targets", [])
    ]
    if "alertmanager:9093" not in alert_targets:
        fail("prometheus alertmanager target missing")

# 2. SLO alert rules -----------------------------------------------------------
rules = load_yaml(obs / "alert-rules.yml")
REQUIRED_ALERTS = (
    "ServiceDown",
    "HighErrorRate",
    "SlowP95Latency",
    "QueueStarvation",
    "QueueFailureSpike",
    "StuckRunningJobs",
)
if rules:
    present = {
        rule.get("alert")
        for group in rules.get("groups", [])
        for rule in group.get("rules", [])
    }
    for alert in REQUIRED_ALERTS:
        if alert not in present:
            fail(f"alert rule '{alert}' missing")

# 3. Alert expressions reference real metric names ------------------------------
metrics_src = (
    Path("libs/backend-core/src/atoz_backend_core/observability/metrics.py").read_text()
    + Path("services/automation-service/src/atoz_automation_service/observability.py").read_text()
)
rule_text = (obs / "alert-rules.yml").read_text()
for metric in ("http_requests_total", "http_request_duration_seconds", "atoz_queue_items", "atoz_job_runs"):
    if metric not in metrics_src:
        fail(f"alert metric '{metric}' not defined in service code")
    if metric not in rule_text:
        fail(f"alert rules do not use metric '{metric}'")

# 4. Grafana provisioning -------------------------------------------------------
ds = load_yaml(obs / "grafana/provisioning/datasources/datasources.yml")
if ds:
    names = {d.get("name") for d in ds.get("datasources", [])}
    for name in ("Prometheus", "Loki"):
        if name not in names:
            fail(f"grafana datasource '{name}' missing")
dashboards_cfg = load_yaml(obs / "grafana/provisioning/dashboards/dashboards.yml")
if dashboards_cfg and not (obs / "grafana/dashboards/ops.json").exists():
    fail("grafana ops dashboard json missing")
try:
    json.loads((obs / "grafana/dashboards/ops.json").read_text())
except Exception as exc:  # noqa: BLE001
    fail(f"invalid grafana dashboard JSON: {exc}")

# 5. Loki + Promtail -------------------------------------------------------------
loki_cfg = load_yaml(obs / "loki.yml")
if loki_cfg is None:
    fail("loki.yml invalid")
promtail = load_yaml(obs / "promtail.yml")
if promtail:
    client_urls = [c.get("url", "") for c in promtail.get("clients", [])]
    if not any("loki:3100" in u for u in client_urls):
        fail("promtail does not push to loki:3100")
    has_docker_sd = any(
        cfg.get("job_name") == "docker" and cfg.get("docker_sd_configs")
        for cfg in promtail.get("scrape_configs", [])
    )
    if not has_docker_sd:
        fail("promtail docker_sd_configs missing")

# 6. OTel collector ---------------------------------------------------------------
otel = load_yaml(obs / "otel-collector.yml")
if otel:
    receivers = otel.get("receivers", {}).get("otlp", {})
    if not receivers:
        fail("otel-collector has no otlp receiver")
    pipelines = otel.get("service", {}).get("pipelines", {})
    if not pipelines.get("traces"):
        fail("otel-collector has no traces pipeline")

# 7. Request IDs + credentials in logs --------------------------------------------
logging_src = Path("libs/backend-core/src/atoz_backend_core/logging.py").read_text()
request_id_src = Path("libs/backend-core/src/atoz_backend_core/middleware/request_id.py").read_text()
if "request_id" not in logging_src:
    fail("structured logging does not include request_id")
if "X-Request-ID" not in request_id_src:
    fail("request-id middleware does not propagate X-Request-ID")
if "model_dump" in logging_src or "dict(self" in logging_src:
    fail("structured logging must not dump raw settings/credentials")

if violations:
    print(f"Observability guard failed with {violations} violation(s).")
    sys.exit(1)
print("Observability guard: OK")
PY
