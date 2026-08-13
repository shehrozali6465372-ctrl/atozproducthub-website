"""Migration/clean-database tests for automation_db.

Runs ``alembic upgrade head`` against a fresh SQLite file database, verifies
the full schema, exercises a smoke INSERT/SELECT, then downgrades and
re-upgrades to prove the migration is repeatable. The CI ``database`` job
runs the same revision against a fresh PostgreSQL 16 database.

The migration stream intentionally creates only automation-owned tables
(ADR-0010); Platform tables (scheduled_jobs, job_runs, queue_items) are
created by the admin-service stream and are not expected here.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

from atoz_automation_service.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"

EXPECTED_TABLES = {
    "automation_niches",
    "automation_rules",
    "automation_runs",
    "aios_job_records",
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
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'automation.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        command.upgrade(_alembic_config(database_url), "head")
        tables = _tables(database_url)
        assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"
        # Platform tables are NOT created by the automation stream.
        assert not {"scheduled_jobs", "job_runs", "queue_items"} & tables

        # Smoke INSERT/SELECT through the migrated schema.
        import asyncio

        from atoz_automation_service.domain.entities import (
            AiosJobRecord,
            AutomationNiche,
            AutomationRule,
        )
        from atoz_automation_service.uuids import uuid7

        async def smoke() -> None:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            engine = create_async_engine(database_url)
            try:
                session_factory = async_sessionmaker(engine, expire_on_commit=False)
                async with session_factory() as session:
                    niche = AutomationNiche(id=uuid7(), name="Smoke", slug="smoke", status="active")
                    session.add(niche)
                    await session.flush()
                    rule = AutomationRule(
                        id=uuid7(),
                        niche_id=niche.id,
                        code="smoke-rule",
                        trigger_type="manual",
                        config_json="{}",
                        status="disabled",
                    )
                    session.add(rule)
                    await session.flush()
                    session.add(
                        AiosJobRecord(
                            id=uuid7(),
                            niche_id=niche.id,
                            job_id="smoke-job",
                            contract="AIOS.Content.Intake",
                            direction="outbound",
                            status="pending",
                            attempts=0,
                        )
                    )
                    await session.commit()
                async with session_factory() as session:
                    rows = (
                        await session.execute(__import__("sqlalchemy").select(AutomationRule.code))
                    ).scalars()
                    assert list(rows) == ["smoke-rule"]
            finally:
                await engine.dispose()

        asyncio.run(smoke())

        # Downgrade removes every automation table, upgrade restores them.
        command.downgrade(_alembic_config(database_url), "base")
        assert _tables(database_url) <= {"alembic_version_automation"}

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
