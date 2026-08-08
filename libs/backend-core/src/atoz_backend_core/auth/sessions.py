"""Session manager: active sessions with expiry and revocation.

In-memory for dev/tests; Redis-backed for production. Sessions store a
subject, a permissions snapshot, and MFA state — revocation is immediate.
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import redis.asyncio as aioredis


@dataclass
class Session:
    session_id: str
    subject: str
    permissions: tuple[str, ...] = ()
    mfa_verified: bool = False
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0

    @property
    def expired(self) -> bool:
        return self.expires_at > 0 and time.time() > self.expires_at


class SessionManager(ABC):
    """Session lifecycle: create, resolve, revoke."""

    @abstractmethod
    async def create(
        self,
        *,
        subject: str,
        permissions: tuple[str, ...] = (),
        ttl_seconds: int,
        mfa_verified: bool = False,
    ) -> Session: ...

    @abstractmethod
    async def get(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def revoke(self, session_id: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_subject(self, subject: str) -> None: ...


class InMemorySessionManager(SessionManager):
    """Thread-safe in-memory store (dev and tests)."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    async def create(self, *, subject, permissions=(), ttl_seconds, mfa_verified=False) -> Session:
        now = time.time()
        session = Session(
            session_id=uuid.uuid4().hex,
            subject=subject,
            permissions=permissions,
            mfa_verified=mfa_verified,
            created_at=now,
            expires_at=now + ttl_seconds,
        )
        self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None or session.expired:
            return None
        return session

    async def revoke(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def revoke_all_for_subject(self, subject: str) -> None:
        for sid in [sid for sid, s in self._sessions.items() if s.subject == subject]:
            self._sessions.pop(sid, None)


class RedisSessionManager(SessionManager):
    """Redis-backed sessions (production): key ``sessions:{id}`` with TTL."""

    def __init__(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def create(self, *, subject, permissions=(), ttl_seconds, mfa_verified=False) -> Session:
        session = Session(
            session_id=uuid.uuid4().hex,
            subject=subject,
            permissions=permissions,
            mfa_verified=mfa_verified,
            expires_at=time.time() + ttl_seconds,
        )
        payload = json.dumps(
            {
                "subject": session.subject,
                "permissions": list(session.permissions),
                "mfa_verified": session.mfa_verified,
                "expires_at": session.expires_at,
            }
        )
        await self._redis.set(f"sessions:{session.session_id}", payload, ex=ttl_seconds)
        return session

    async def get(self, session_id: str) -> Session | None:
        payload = await self._redis.get(f"sessions:{session_id}")
        if not payload:
            return None
        data = json.loads(payload)
        return Session(
            session_id=session_id,
            subject=data["subject"],
            permissions=tuple(data.get("permissions") or ()),
            mfa_verified=bool(data.get("mfa_verified")),
            expires_at=float(data["expires_at"]),
        )

    async def revoke(self, session_id: str) -> None:
        await self._redis.delete(f"sessions:{session_id}")

    async def revoke_all_for_subject(self, subject: str) -> None:
        # Scans are O(N); acceptable until session sets are sharded (Phase 5).
        async for key in self._redis.scan_iter(match="sessions:*"):
            payload = await self._redis.get(key)
            if payload and json.loads(payload).get("subject") == subject:
                await self._redis.delete(key)
