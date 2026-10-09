"""Content storage abstraction (Database Blueprint §2.1).

Bodies and media never live in the database: the database stores
``content_ref`` (object-storage key) + ``content_checksum``. M4 ships the
local (filesystem) and in-memory (tests) implementations; Phase 6 swaps in
the R2/S3 implementation behind the same protocol.
"""

import hashlib
from pathlib import Path
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ContentStore(Protocol):
    """Put/get content blobs by object-storage key."""

    async def put(self, *, ref: str, content: str) -> None: ...

    async def get(self, ref: str) -> str | None: ...


def checksum_of(content: str) -> str:
    """SHA-256 hex digest used for content dedupe and integrity checks."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class LocalContentStore:
    """Filesystem implementation (dev/local; CWD-relative directory)."""

    def __init__(self, directory: str | Path) -> None:
        self._root = Path(directory)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
        # Refs are service-generated (``articles/<id>/v<N>.txt``); guard
        # against traversal regardless.
        safe = Path(ref)
        if safe.is_absolute() or ".." in safe.parts:
            raise ValueError(f"Unsafe content ref: {ref!r}")
        return self._root / safe

    async def put(self, *, ref: str, content: str) -> None:
        path = self._path(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    async def get(self, ref: str) -> str | None:
        path = self._path(ref)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")


class InMemoryContentStore:
    """Test/CI implementation — no filesystem access."""

    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    async def put(self, *, ref: str, content: str) -> None:
        self._items[ref] = content

    async def get(self, ref: str) -> str | None:
        return self._items.get(ref)


class DatabaseContentStore:
    """PostgreSQL-backed blob store for persistent production article bodies.

    Render's free web-service filesystem is ephemeral, so production content
    must be stored in the managed database rather than the container disk.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def put(self, *, ref: str, content: str) -> None:
        checksum = checksum_of(content)
        async with self._session_factory() as session:
            await session.execute(
                text(
                    "INSERT INTO content_blobs (content_ref, body, checksum) "
                    "VALUES (:ref, :body, :checksum) "
                    "ON CONFLICT (content_ref) DO UPDATE SET "
                    "body = EXCLUDED.body, checksum = EXCLUDED.checksum, updated_at = now()"
                ),
                {"ref": ref, "body": content, "checksum": checksum},
            )
            await session.commit()

    async def get(self, ref: str) -> str | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT body FROM content_blobs WHERE content_ref = :ref"),
                {"ref": ref},
            )
            body = result.scalar_one_or_none()
            return str(body) if body is not None else None
