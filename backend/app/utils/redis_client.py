"""
Redis client — handles JWT blacklisting, prediction caching, and rate limiting.
"""

import json
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()


class RedisClient:
    """Async Redis client wrapper for all Redis operations."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis. Called on app startup."""
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self):
        """Close Redis connection. Called on app shutdown."""
        if self._redis:
            await self._redis.close()

    # ── JWT Blacklisting ──

    async def blacklist_token(self, jti: str, ttl_seconds: int):
        """Add a token's JTI to the blacklist with TTL matching its remaining lifetime."""
        await self._redis.setex(f"blacklist:{jti}", ttl_seconds, "1")

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token's JTI is blacklisted."""
        return await self._redis.exists(f"blacklist:{jti}") > 0

    # ── Prediction Caching ──

    async def cache_prediction(self, image_hash: str, result: dict, ttl: int = 3600):
        """Cache a prediction result by image hash (TTL: 1 hour)."""
        await self._redis.setex(
            f"prediction:{image_hash}", ttl, json.dumps(result)
        )

    async def get_cached_prediction(self, image_hash: str) -> Optional[dict]:
        """Get a cached prediction by image hash. Returns None if not cached."""
        cached = await self._redis.get(f"prediction:{image_hash}")
        if cached:
            return json.loads(cached)
        return None

    # ── Rate Limiting ──

    async def check_rate_limit(self, user_id: str, max_requests: int = 10) -> bool:
        """
        Check and increment the rate limit counter for a user.
        Returns True if the request is ALLOWED, False if RATE LIMITED.
        """
        key = f"rate:{user_id}"
        current = await self._redis.get(key)

        if current is None:
            # First request in this window — set counter to 1, expire in 60 seconds
            await self._redis.setex(key, 60, 1)
            return True

        if int(current) >= max_requests:
            return False

        # Increment the counter
        await self._redis.incr(key)
        return True


# Singleton instance — imported by other modules
redis_client = RedisClient()
