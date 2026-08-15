"""Observability verification tests (Task 24 Phase G)."""

import json
import logging
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "infra/observability"

REQUIRED_ALERTS = (
    "ServiceDown",
    "HighErrorRate",
    "SlowP95Latency",
    "QueueStarvation",
    "QueueFailureSpike",
    "StuckRunningJobs",
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_prometheus_scrapes_every_service() -> None:
    config = _load_yaml(OBS / "prometheus.yml")
    targets = [
        target
        for job in config["scrape_configs"]
        for cfg in job.get("static_configs", [])
        for target in cfg.get("targets", [])
    ]
    for service in (
        "api",
        "aios-bridge",
        "content-service",
        "affiliate-service",
        "pinterest-service",
        "seo-service",
        "analytics-service",
        "admin-service",
        "automation-service",
    ):
        assert any(str(t).startswith(f"{service}:") for t in targets), service


def test_prometheus_alerts_alertmanager() -> None:
    config = _load_yaml(OBS / "prometheus.yml")
    targets = [
        target
        for am in config["alerting"]["alertmanagers"]
        for cfg in am.get("static_configs", [])
        for target in cfg.get("targets", [])
    ]
    assert "alertmanager:9093" in targets


def test_all_slo_alerts_exist() -> None:
    rules = _load_yaml(OBS / "alert-rules.yml")
    present = {rule.get("alert") for group in rules["groups"] for rule in group.get("rules", [])}
    assert set(REQUIRED_ALERTS) <= present


def test_alert_metrics_are_defined_in_code() -> None:
    metric_src = (
        ROOT / "libs/backend-core/src/atoz_backend_core/observability/metrics.py"
    ).read_text()
    automation_src = (
        ROOT / "services/automation-service/src/atoz_automation_service/observability.py"
    ).read_text()
    rule_text = (OBS / "alert-rules.yml").read_text()
    for metric in (
        "http_requests_total",
        "http_request_duration_seconds",
        "atoz_queue_items",
        "atoz_job_runs",
    ):
        assert metric in metric_src + automation_src, metric
        assert metric in rule_text, metric


def test_grafana_provisioning_loads() -> None:
    datasources = _load_yaml(OBS / "grafana/provisioning/datasources/datasources.yml")
    names = {d.get("name") for d in datasources["datasources"]}
    assert {"Prometheus", "Loki"} <= names
    dashboard = json.loads((OBS / "grafana/dashboards/ops.json").read_text())
    assert dashboard.get("title")
    assert dashboard.get("panels")


def test_loki_receives_structured_logs_via_promtail() -> None:
    loki = _load_yaml(OBS / "loki.yml")
    assert loki is not None
    promtail = _load_yaml(OBS / "promtail.yml")
    urls = [c.get("url", "") for c in promtail["clients"]]
    assert any("loki:3100" in url for url in urls)
    jobs = {cfg.get("job_name") for cfg in promtail["scrape_configs"]}
    assert "docker" in jobs


def test_otel_collector_accepts_otlp() -> None:
    otel = _load_yaml(OBS / "otel-collector.yml")
    assert otel["receivers"]["otlp"]["protocols"]["http"]["endpoint"] == "0.0.0.0:4318"
    assert "traces" in otel["service"]["pipelines"]


def test_request_ids_correlate_structured_logs() -> None:
    from atoz_backend_core.logging import JsonFormatter, request_id_var

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    request_id_var.set("req-123")
    try:
        payload = json.loads(JsonFormatter(service="s", env="test").format(record))
    finally:
        request_id_var.set(None)
    assert payload["request_id"] == "req-123"
    assert "password" not in payload and "secret" not in payload


def test_log_format_never_dumps_raw_settings() -> None:
    logging_src = (ROOT / "libs/backend-core/src/atoz_backend_core/logging.py").read_text()
    assert "model_dump" not in logging_src
    assert "dict(self" not in logging_src
