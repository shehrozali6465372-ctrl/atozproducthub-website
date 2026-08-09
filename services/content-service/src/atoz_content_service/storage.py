"""Content storage abstraction (Database Blueprint §2.1).

Bodies and media never live in the database: the database stores
``content_ref`` (object-storage key) + ``content_checksum``. M4 ships the
local (filesystem) and in-memory (tests) implementations; Phase 6 swaps in
the R2/S3 implementation behind the same protocol.
"""

import hashlib
from pathlib import Path
from typing import Protocol


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
