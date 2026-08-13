"""Migration/clean-database tests for admin_db.

Runs ``alembic upgrade head`` against a fresh SQLite file database, verifies
the full schema, exercises a smoke INSERT/SELECT, then downgrades and
re-upgrades to prove the migration is repeatable. The CI ``database`` job
runs the same revision against a fresh PostgreSQL 16 database.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

from atoz_admin_service.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"

EXPECTED_TABLES = {
    "admin_niches",
    "admin_users",
    "roles",
    "permissions",
    "role_permissions",
    "user_roles",
    "api_keys",
    "admin_preferences",
    "audit_logs",
    "notifications",
    "notification_preferences",
    "notification_deliveries",
    "queue_items",
    "webhook_logs",
    "operation_logs",
    "scheduled_jobs",
    "job_runs",
}


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(MIGRATIONS_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def _tables(database_url: str) -> set[str]:
    import sqlalchemy as sa

    sync_url = database_url.replace("sqlite+aiosqlite", "sqlite")
    engine = sa.create_engine(sync_url)
    try:
        with engine.connect() as conn:
            if database_url.startswith("sqlite"):
                result = conn.execute(
                    sa.text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                )
            else:
                result = conn.execute(
                    sa.text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            return {row[0] for row in result}
    finally:
        engine.dispose()


def test_migrations_upgrade_downgrade_upgrade_on_clean_database(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'admin.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        command.upgrade(_alembic_config(database_url), "head")
        tables = _tables(database_url)
        assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"

        # Smoke INSERT/SELECT through the migrated schema.
        import asyncio

        from atoz_admin_service.domain.entities import AdminUser, AuditLog
        from atoz_admin_service.uuids import uuid7

        async def smoke() -> None:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            engine = create_async_engine(database_url)
            try:
                session_factory = async_sessionmaker(engine, expire_on_commit=False)
                async with session_factory() as session:
                    user = AdminUser(
                        id=uuid7(),
                        subject="smoke",
                        email="smoke@example.com",
                        display_name="Smoke",
                        status="active",
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        AuditLog(
                            id=uuid7(),
                            action="create",
                            entity_type="admin_user",
                            entity_id=user.id,
                            admin_user_id=user.id,
                        )
                    )
                    await session.commit()
                async with session_factory() as session:
                    rows = (
                        await session.execute(__import__("sqlalchemy").select(AuditLog.action))
                    ).scalars()
                    assert list(rows) == ["create"]
            finally:
                await engine.dispose()

        asyncio.run(smoke())

        # Downgrade removes every table, upgrade restores them (repeatable).
        command.downgrade(_alembic_config(database_url), "base")
        assert _tables(database_url) <= {"alembic_version_admin"}

        command.upgrade(_alembic_config(database_url), "head")
        assert EXPECTED_TABLES <= _tables(database_url)
    finally:
        get_settings.cache_clear()


def test_migration_revision_is_single_head() -> None:
    from alembic.script import ScriptDirectory

    cfg = _alembic_config("sqlite+aiosqlite:///:memory:")
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert len(heads) == 1
    assert heads == ["0001"]
