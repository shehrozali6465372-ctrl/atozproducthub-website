"""Unit of Work: transaction boundary for service use cases.

``SqlAlchemyUnitOfWork`` scopes one async session per unit; commits on
success, rolls back on error. Services compose repositories inside a single
UoW so a business operation is atomic.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

RepositoryT = TypeVar("RepositoryT")


class UnitOfWork(ABC):
    """Transaction boundary contract."""

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Async SQLAlchemy UoW; repositories are created from a factory."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        repositories: dict[str, Any] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._repositories = repositories or {}

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UoW session accessed outside the transaction context")
        return self._session

    async def _open(self) -> None:
        if self._session is None:
            self._session = self._session_factory()
            for name, factory in self._repositories.items():
                setattr(self, name, factory(self._session))

    async def commit(self) -> None:
        await self._open()
        await self.session.commit()

    async def rollback(self) -> None:
        await self._open()
        await self.session.rollback()

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["SqlAlchemyUnitOfWork"]:
        await self._open()
        try:
            yield self
            await self.session.commit()
        except BaseException:
            await self.session.rollback()
            raise
