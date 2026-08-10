"""Migration/clean-database tests for affiliate_db.

Runs ``alembic upgrade head`` against a fresh SQLite file database, verifies
the full schema, exercises a smoke INSERT/SELECT, then downgrades and
re-upgrades to prove the migration is repeatable. The CI ``database`` job
runs the same revision against a fresh PostgreSQL 16 database.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

from atoz_affiliate_service.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"

EXPECTED_TABLES = {
    "affiliate_niches",
    "affiliate_networks",
    "affiliate_merchants",
    "product_categories",
    "affiliate_products",
    "product_category_links",
    "affiliate_links",
    "link_tokens",
    "click_attributions",
    "affiliate_clicks",
    "revenue_transactions",
    "revenue_reconciliations",
    "revenue_summaries",
    "affiliate_webhook_logs",
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
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'affiliate.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        command.upgrade(_alembic_config(database_url), "head")
        tables = _tables(database_url)
        assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"

        # Smoke INSERT/SELECT through the migrated schema.
        import asyncio

        from atoz_affiliate_service.domain.entities import (
            AffiliateNetwork,
            AffiliateNiche,
            AffiliateProduct,
        )
        from atoz_affiliate_service.uuids import uuid7

        async def smoke() -> None:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            engine = create_async_engine(database_url)
            try:
                session_factory = async_sessionmaker(engine, expire_on_commit=False)
                async with session_factory() as session:
                    niche = AffiliateNiche(id=uuid7(), name="Smoke", slug="smoke", status="active")
                    session.add(niche)
                    await session.flush()
                    network = AffiliateNetwork(
                        id=uuid7(), code="amazon", name="Amazon", status="active"
                    )
                    session.add(network)
                    await session.flush()
                    session.add(
                        AffiliateProduct(
                            id=uuid7(),
                            niche_id=niche.id,
                            merchant_id="00000000-0000-7000-8000-000000000001",
                            sku="SKU-1",
                            slug="smoke-product",
                            name="Smoke",
                            price_cents=100,
                            currency="USD",
                            status="draft",
                        )
                    )
                    await session.commit()
                async with session_factory() as session:
                    rows = (
                        await session.execute(
                            __import__("sqlalchemy").select(AffiliateProduct.slug)
                        )
                    ).scalars()
                    assert list(rows) == ["smoke-product"]
            finally:
                await engine.dispose()

        asyncio.run(smoke())

        # Downgrade removes every table, upgrade restores them (repeatable).
        command.downgrade(_alembic_config(database_url), "base")
        assert _tables(database_url) <= {"alembic_version"}

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
