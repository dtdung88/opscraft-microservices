import redis.asyncio as redis
from typing import Any, Optional
import hashlib
from functools import wraps
import pickle
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-level cache with L1 (memory) and L2 (Redis)"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.l1_cache: dict = {}
        self.l1_max_size = 1000

    async def get(self, key: str) -> Optional[Any]:
        """Get from L1, then L2"""
        if key in self.l1_cache:
            return self.l1_cache[key]

        try:
            value = await self.redis.get(key)
            if value:
                deserialized = pickle.loads(value)
                if len(self.l1_cache) < self.l1_max_size:
                    self.l1_cache[key] = deserialized
                return deserialized
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set in both L1 and L2"""
        try:
            if len(self.l1_cache) < self.l1_max_size:
                self.l1_cache[key] = value
            serialized = pickle.dumps(value)
            await self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str):
        """Delete from both levels"""
        self.l1_cache.pop(key, None)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern"""
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                    for key in keys:
                        key_str = key.decode() if isinstance(key, bytes) else key
                        self.l1_cache.pop(key_str, None)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5((str(args) + str(kwargs)).encode()).hexdigest()}"

            cache_manager = kwargs.get('cache_manager')
            if not cache_manager:
                return await func(*args, **kwargs)

            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator