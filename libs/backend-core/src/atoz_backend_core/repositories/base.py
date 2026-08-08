"""Repository pattern: CRUD interfaces + SQLAlchemy implementation.

Domain repositories in services extend these generic contracts; business
rules stay in the services, never in this library.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

Entity = TypeVar("Entity")
Id = TypeVar("Id")


class Repository(ABC, Generic[Entity, Id]):
    """Generic CRUD contract implemented by every service repository."""

    @abstractmethod
    async def get(self, entity_id: Id) -> Entity | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[Entity]: ...

    @abstractmethod
    async def add(self, entity: Entity) -> Entity: ...

    @abstractmethod
    async def update(self, entity: Entity) -> Entity: ...

    @abstractmethod
    async def delete(self, entity_id: Id) -> bool: ...

    async def exists(self, entity_id: Id) -> bool:
        return await self.get(entity_id) is not None

    async def count(self) -> int:
        return len(await self.list())


class SqlAlchemyRepository(Repository[Entity, Id], Generic[Entity, Id]):
    """Async SQLAlchemy implementation bound to a session (from UoW)."""

    model: type[Entity]  # assigned by subclasses in services

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: Id) -> Entity | None:
        return await self._session.get(self.model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[Entity]:
        from sqlalchemy import select

        result = await self._session.scalars(select(self.model).limit(limit).offset(offset))
        return result.all()

    async def add(self, entity: Entity) -> Entity:
        self._session.add(entity)
        return entity

    async def update(self, entity: Entity) -> Entity:
        await self._session.merge(entity)
        return entity

    async def delete(self, entity_id: Id) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        return True
