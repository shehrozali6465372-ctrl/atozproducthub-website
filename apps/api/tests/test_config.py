"""Configuration and environment-loading tests."""

import pytest
from pydantic import ValidationError

from atoz_api.config import Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.app_env == "dev"
    assert settings.app_name == "AtozProductHub API"
    assert settings.app_port == 8000
    assert settings.app_log_level == "INFO"


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
    settings = Settings(_env_file=None)
    assert settings.app_env == "staging"
    assert settings.app_port == 9000
    assert settings.app_log_level == "DEBUG"


def test_production_flag() -> None:
    assert Settings(_env_file=None).is_production is False
    settings = Settings(_env_file=None, app_env="prod")
    assert settings.is_production is True


def test_invalid_env_rejected(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "nope")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
