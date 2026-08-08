"""Repository pattern + unit of work on async SQLite (StaticPool)."""

import asyncio
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from atoz_backend_core.db.base import Base
from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class WidgetRepository(SqlAlchemyRepository[Widget, str]):
    model = Widget


def run_scenario(
    scenario: Callable[[async_sessionmaker[AsyncSession]], Awaitable[None]],
) -> None:
    """Run an async scenario against a fresh in-memory SQLite database.

    Engine, connections, and teardown all live in the same event loop, so
    aiosqlite never crosses loop boundaries.
    """

    async def runner() -> None:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        try:
            await scenario(async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(runner())


def test_repository_crud() -> None:
    async def scenario(session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            repo = WidgetRepository(session)
            await repo.add(Widget(id="w1", name="first"))
            await session.commit()

        async with session_factory() as session:
            repo = WidgetRepository(session)
            widget = await repo.get("w1")
            assert widget is not None and widget.name == "first"
            assert await repo.count() == 1
            assert [w.id for w in await repo.list()] == ["w1"]
            widget.name = "renamed"
            await repo.update(widget)
            await session.commit()

        async with session_factory() as session:
            repo = WidgetRepository(session)
            widget = await repo.get("w1")
            assert widget is not None and widget.name == "renamed"
            assert await repo.delete("w1") is True
            await session.commit()

        async with session_factory() as session:
            assert await WidgetRepository(session).get("w1") is None

    run_scenario(scenario)


def test_unit_of_work_transaction() -> None:
    async def scenario(session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory, repositories={"widgets": WidgetRepository})
        async with uow.transaction() as unit:
            await unit.widgets.add(Widget(id="w2", name="second"))

        async with session_factory() as session:
            rows = (await session.scalars(select(Widget))).all()
            assert {w.id for w in rows} == {"w2"}

    run_scenario(scenario)


def test_unit_of_work_rollback_on_error() -> None:
    async def scenario(session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory, repositories={"widgets": WidgetRepository})
        with pytest.raises(RuntimeError):
            async with uow.transaction() as unit:
                await unit.widgets.add(Widget(id="w3", name="third"))
                raise RuntimeError("boom")

        async with session_factory() as session:
            assert await WidgetRepository(session).get("w3") is None

    run_scenario(scenario)
