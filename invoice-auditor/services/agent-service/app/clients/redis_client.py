"""
Agent Service - Redis Client

Provides an asynchronous connection pool to Redis for caching
translations and LLM outputs.
"""

import logging
from typing import Optional

import redis.asyncio as redis

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool instance
redis_client: Optional[redis.Redis] = None


async def start_redis() -> None:
    """Initialize the Redis connection pool."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
            # Test connection
            await redis_client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # We don't raise here, to allow the app to start without Redis (graceful degradation)
            redis_client = None


async def stop_redis() -> None:
    """Close the Redis connection pool."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
        logger.info("Redis connection closed.")


def get_redis() -> Optional[redis.Redis]:
    """Get the active Redis client (can be None if connection failed)."""
    return redis_client
