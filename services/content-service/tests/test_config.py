"""Content-service settings tests."""

from atoz_content_service.config import Settings


def test_defaults() -> None:
    settings = Settings(app_env="test")
    assert settings.app_name == "AtozProductHub Content Service"
    assert settings.admin_read_permission == "content:read"
    assert settings.admin_write_permission == "content:write"
    assert settings.default_page_size == 20
    assert settings.max_page_size == 100
    assert settings.public_base_url == "https://atozproducthub.com"


def test_env_loading(monkeypatch) -> None:
    from atoz_content_service.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://db")
    monkeypatch.setenv("JWT_SECRET", "env-secret-value")
    monkeypatch.setenv("MAX_PAGE_SIZE", "50")
    settings = get_settings()
    try:
        assert settings.database_url == "postgresql+asyncpg://db"
        assert settings.jwt_secret == "env-secret-value"
        assert settings.max_page_size == 50
    finally:
        get_settings.cache_clear()
