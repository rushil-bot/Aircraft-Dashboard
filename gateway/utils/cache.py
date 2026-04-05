"""Redis and memory cache abstraction component rules."""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger("gateway.cache")


class CacheService:
    """
    Abstracts caching logic (Redis with in-memory fallback).
    Follows SRP by isolating caching strategy from business logic.
    """

    TTL = 60 * 10  # 10 minutes

    def __init__(self):
        self._redis_client = None
        self._memory_cache: dict[str, tuple[float, dict]] = {}

    async def connect(self):
        """Intialize Redis connection."""
        try:
            import redis.asyncio as aioredis  # pylint: disable=import-outside-toplevel,import-error

            redis_host = os.environ.get("REDIS_HOST", "localhost")
            redis_port = int(os.environ.get("REDIS_PORT", "6379"))
            self._redis_client = aioredis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            await self._redis_client.ping()
            logger.info("[PASS] Connected to Redis")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("[WARN] Redis unavailable (%s)", e)
            self._redis_client = None

    async def close(self):
        """Close cache connections."""
        if self._redis_client:
            await self._redis_client.close()

    async def get(self, key: str) -> Optional[dict]:
        """Retrieve value from cache."""
        if self._redis_client:
            raw = await self._redis_client.get(key)
            if raw:
                return json.loads(raw)
            return None

        # In-memory fallback
        if key in self._memory_cache:
            ts, data = self._memory_cache[key]
            if time.time() - ts < self.TTL:
                return data
            del self._memory_cache[key]
        return None

    async def set(self, key: str, data: dict):
        """Store value in cache."""
        if self._redis_client:
            await self._redis_client.setex(key, self.TTL, json.dumps(data))
        else:
            self._memory_cache[key] = (time.time(), data)

    @property
    def mode(self) -> str:
        """Return the current cache mode."""
        return "redis" if self._redis_client else "memory"


# Singleton instance
cache = CacheService()
