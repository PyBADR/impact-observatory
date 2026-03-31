"""
Redis client wrapper for caching and async task queue.
"""

from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis
import logging

from app.config.settings import Settings

logger = logging.getLogger(__name__)


async def get_redis(settings: Settings) -> Redis:
    """
    Create and return Redis async client.

    Args:
        settings: Application settings with Redis configuration

    Returns:
        Configured Redis async client
    """
    client = await aioredis.from_url(
        settings.redis_url,
        encoding="utf8",
        decode_responses=True,
        max_connections=settings.redis_max_connections,
        socket_keepalive=settings.redis_socket_keepalive,
        socket_keepalive_options=settings.redis_socket_keepalive_options,
    )

    # Test connection
    try:
        await client.ping()
        logger.info("Redis client connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    return client


async def close_redis(client: Redis) -> None:
    """
    Close Redis client connection.

    Args:
        client: Redis client instance to close
    """
    try:
        await client.close()
        logger.info("Redis client closed")
    except Exception as e:
        logger.warning(f"Error closing Redis client: {e}")


async def health_check(client: Redis) -> bool:
    """
    Check Redis connectivity.

    Args:
        client: Redis client instance

    Returns:
        True if Redis is healthy, False otherwise
    """
    try:
        pong = await client.ping()
        return pong is True or pong == "PONG"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Cache key prefixes for namespacing
CACHE_PREFIXES = {
    "events": "events:",
    "incidents": "incidents:",
    "alerts": "alerts:",
    "predictions": "predictions:",
    "signals": "signals:",
    "session": "session:",
}


async def cache_set(
    client: Redis,
    key: str,
    value: str,
    ttl: Optional[int] = 3600,
) -> bool:
    """
    Set cache value with optional TTL.

    Args:
        client: Redis client
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default 1 hour)

    Returns:
        True if set successfully
    """
    try:
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Failed to set cache key {key}: {e}")
        return False


async def cache_get(client: Redis, key: str) -> Optional[str]:
    """
    Get value from cache.

    Args:
        client: Redis client
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        return await client.get(key)
    except Exception as e:
        logger.error(f"Failed to get cache key {key}: {e}")
        return None


async def cache_delete(client: Redis, key: str) -> bool:
    """
    Delete cache key.

    Args:
        client: Redis client
        key: Cache key to delete

    Returns:
        True if deleted
    """
    try:
        await client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete cache key {key}: {e}")
        return False


async def cache_clear_prefix(client: Redis, prefix: str) -> int:
    """
    Clear all keys matching a prefix pattern.

    Args:
        client: Redis client
        prefix: Key prefix to clear (e.g., "events:")

    Returns:
        Number of keys deleted
    """
    try:
        keys = await client.keys(f"{prefix}*")
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Failed to clear cache prefix {prefix}: {e}")
        return 0
