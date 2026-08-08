"""Database health checks (not configured until Phase 4)."""

import asyncio

from atoz_backend_core.db.postgres import check_database
from atoz_backend_core.db.redis import check_redis


def test_check_database_not_configured() -> None:
    assert asyncio.run(check_database(None)) == {
        "name": "postgres",
        "status": "not_configured",
    }


def test_check_redis_not_configured() -> None:
    assert asyncio.run(check_redis(None)) == {
        "name": "redis",
        "status": "not_configured",
    }
