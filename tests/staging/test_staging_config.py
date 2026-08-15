"""Staging environment configuration tests (Task 24 / M11 Phase 3)."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_SERVICES = [
    "api",
    "aios-bridge",
    "content-service",
    "affiliate-service",
    "pinterest-service",
    "seo-service",
    "analytics-service",
    "admin-service",
    "automation-service",
    "automation-worker",
    "automation-beat",
    "postgres",
    "redis",
    "kafka",
    "clickhouse",
    "typesense",
    "proxy",
    "otel-collector",
    "prometheus",
    "alertmanager",
    "grafana",
    "loki",
    "promtail",
]

FIRST_PARTY = [
    "api",
    "aios-bridge",
    "content-service",
    "affiliate-service",
    "pinterest-service",
    "seo-service",
    "analytics-service",
    "admin-service",
    "automation-service",
    "automation-worker",
    "automation-beat",
]


@pytest.fixture(scope="module")
def prod_compose() -> dict:
    return yaml.safe_load((ROOT / "infra/docker/compose.prod.yml").read_text())


@pytest.fixture(scope="module")
def staging_overlay() -> dict:
    return yaml.safe_load((ROOT / "infra/docker/compose.staging.yml").read_text())


@pytest.fixture(scope="module")
def staging_template() -> str:
    return (ROOT / "config/staging/env.template").read_text()


def test_all_required_services_present(prod_compose: dict) -> None:
    services = set(prod_compose["services"])
    missing = [name for name in REQUIRED_SERVICES if name not in services]
    assert missing == []


def test_staging_overlay_identity(staging_overlay: dict) -> None:
    assert staging_overlay["name"] == "atozproducthub-staging"
    services = set(staging_overlay["services"])
    prod_services = set(
        yaml.safe_load((ROOT / "infra/docker/compose.prod.yml").read_text())["services"]
    )
    assert services <= prod_services


def test_staging_overlay_sets_app_env(staging_overlay: dict) -> None:
    for name in FIRST_PARTY:
        env = (staging_overlay.get("services", {}).get(name) or {}).get("environment") or {}
        assert env.get("APP_ENV") == "staging", f"{name} must run as APP_ENV=staging"


def test_staging_overlay_publishes_no_host_ports(staging_overlay: dict) -> None:
    for name, service in staging_overlay.get("services", {}).items():
        assert not service.get("ports"), f"staging must not publish host ports ({name})"


def test_staging_overlay_has_no_literal_credentials(staging_overlay: dict) -> None:
    raw = yaml.safe_dump(staging_overlay)
    for token in ("password:", "SECRET=", "API_KEY=", "sk-", "AKIA", "ghp_", "vault://"):
        assert token not in raw, f"staging overlay must not contain '{token}'"


def test_staging_template_documents_all_required_vars(staging_template: str) -> None:
    raw_prod = (ROOT / "infra/docker/compose.prod.yml").read_text()
    required = set(re.findall(r"\$\{([A-Z0-9_]+):\?", raw_prod))
    missing = [var for var in sorted(required) if var not in staging_template]
    assert missing == []


def test_staging_template_env_is_staging(staging_template: str) -> None:
    assert "APP_ENV=staging" in staging_template
