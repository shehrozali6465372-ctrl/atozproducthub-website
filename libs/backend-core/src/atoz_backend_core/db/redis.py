"""Async Redis connection factory and health checks."""

import redis.asyncio as aioredis


def create_redis_client(redis_url: str) -> aioredis.Redis:
    return aioredis.from_url(redis_url, decode_responses=True)


async def check_redis(redis_url: str | None) -> dict[str, object]:
    """Readiness check: ``PING`` against Redis (if configured)."""
    if not redis_url:
        return {"name": "redis", "status": "not_configured"}
    client = create_redis_client(redis_url)
    try:
        await client.ping()
        return {"name": "redis", "status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"name": "redis", "status": "down", "error": str(exc)}
    finally:
        await client.aclose()
