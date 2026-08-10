"""UUID v7 generation (RFC 9562) — shared across business services.

PostgreSQL 18+ ships ``uuidv7()`` and every Postgres 13+ ships
``gen_random_uuid()``, but the standard library has no UUID v7 yet. The
domain layer assigns UUID v7 primary keys itself (Database Blueprint §5:
UUID v7 everywhere); database defaults remain a plain ``gen_random_uuid()``
fallback.

Layout: 48-bit unix-ms timestamp, 4-bit version (7), 12-bit rand_a,
2-bit variant (10), 62-bit rand_b. Monotonic within a process via an
incremented clock sequence when generated in the same millisecond.
"""

import secrets
import time
import uuid

_clock_seq: int = 0
_last_ms: int = -1


def uuid7() -> str:
    """Return a UUID v7 string (time-ordered, random suffix)."""
    global _clock_seq, _last_ms  # noqa: PLW0603

    now_ms = int(time.time() * 1000)
    if now_ms == _last_ms:
        _clock_seq = (_clock_seq + 1) & 0x3FFF
    else:
        _clock_seq = 0
        _last_ms = now_ms

    rand_b = int.from_bytes(secrets.token_bytes(8), "big") & ((1 << 62) - 1)

    value = (now_ms << 80) | ((_clock_seq & 0xFFF) << 64) | rand_b
    value |= 0x7 << 76  # version 7 (bits 76-79)
    value |= 0x2 << 62  # RFC 4122 variant '10' (bits 62-63)

    return str(uuid.UUID(int=value))
