"""Configuration tests."""

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
