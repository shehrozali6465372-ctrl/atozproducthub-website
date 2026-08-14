"""Configuration tests."""

import pytest
from pydantic import ValidationError

from atoz_backend_core.config import BaseServiceSettings


def test_defaults() -> None:
    core_settings = BaseServiceSettings()
    assert core_settings.app_env == "dev"
    assert core_settings.database_url is None
    assert core_settings.redis_url is None
    assert core_settings.is_production is False
    assert core_settings.cors_origins == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]


def test_production_flag() -> None:
    assert BaseServiceSettings(app_env="prod").is_production is True
    assert BaseServiceSettings(app_env="dev").is_production is False


def test_production_rejects_dev_only_secrets() -> None:
    """M11 hardening: prod startup fails when a dev-only default survives."""
    with pytest.raises(ValidationError, match="dev-only"):
        BaseServiceSettings(
            app_env="prod", database_url="postgresql://user:dev-only-db-pw@db:5432/db"
        )


def test_production_rejects_change_me_placeholder() -> None:
    with pytest.raises(ValidationError, match="CHANGE_ME"):
        BaseServiceSettings(
            app_env="prod", database_url="postgresql://atoz:CHANGE_ME@postgres:5432/atoz"
        )


def test_production_accepts_injected_secrets() -> None:
    settings = BaseServiceSettings(
        app_env="prod",
        database_url="postgresql+asyncpg://atoz:secret-value@postgres:5432/atoz",
    )
    assert settings.is_production is True


def test_non_production_allows_dev_defaults() -> None:
    settings = BaseServiceSettings(
        app_env="staging", database_url="postgresql://user:dev-only-pw@db:5432/db"
    )
    assert settings.database_url == "postgresql://user:dev-only-pw@db:5432/db"
