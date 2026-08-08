"""Async PostgreSQL connection factory and health checks (SQLAlchemy 2.0)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    """Create an async engine; no connection is opened until first use."""
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Short-lived session context manager (commit on success, rollback otherwise)."""
    session = session_factory()
    try:
        yield session
        await session.commit()
    except BaseException:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_database(database_url: str | None) -> dict[str, object]:
    """Readiness check: ``SELECT 1`` against PostgreSQL (if configured)."""
    if not database_url:
        return {"name": "postgres", "status": "not_configured"}
    engine = create_engine(database_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"name": "postgres", "status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"name": "postgres", "status": "down", "error": str(exc)}
    finally:
        await engine.dispose()
