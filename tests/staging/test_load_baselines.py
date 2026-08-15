"""Load-test baseline validation (Task 24 Phase F)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_THRESHOLDS = {
    "p50_latency_ms",
    "p95_latency_ms",
    "p99_latency_ms",
    "error_rate_percent",
    "queue_depth_max",
    "worker_processing_time_seconds",
    "database_connection_pressure_max",
}

REQUIRED_SCENARIOS = {
    "health_readiness",
    "public_content_reads",
    "seo_search",
    "affiliate_redirect",
    "analytics_ingestion",
    "admin_read",
    "automation_queue",
}


def test_baselines_yml_is_valid_and_complete() -> None:
    config = yaml.safe_load((ROOT / "tools/loadtest/baselines.yml").read_text())
    assert config["environment"] == "staging"
    assert REQUIRED_THRESHOLDS <= set(config["thresholds"])
    assert REQUIRED_SCENARIOS <= set(config["scenarios"])
    for name, scenario in config["scenarios"].items():
        assert scenario["users"] >= 1
        assert scenario["spawn_rate"] >= 1
        assert scenario["duration_s"] >= 60
        assert scenario["paths"], name


def test_thresholds_match_frozen_slos() -> None:
    config = yaml.safe_load((ROOT / "tools/loadtest/baselines.yml").read_text())
    thresholds = config["thresholds"]
    assert thresholds["p95_latency_ms"] <= 500
    assert thresholds["error_rate_percent"] <= 1.0


def test_locust_profile_covers_every_baseline_scenario() -> None:
    locust = (ROOT / "tools/loadtest/locustfile.py").read_text()
    mapping = {
        "health_readiness": "class HealthUser",
        "public_content_reads": "class ReaderUser",
        "seo_search": "class ReaderUser",
        "affiliate_redirect": "class ReaderUser",
        "analytics_ingestion": "class AnalyticsIngestionUser",
        "admin_read": "class OperatorUser",
        "automation_queue": "class AutomationQueueUser",
    }
    for scenario, marker in mapping.items():
        assert marker in locust, scenario
