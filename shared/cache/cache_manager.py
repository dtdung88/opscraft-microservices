import redis.asyncio as redis
from typing import Any, Optional
import json
import hashlib
from functools import wraps
import pickle

class CacheManager:
    """Multi-level cache with L1 (memory) and L2 (Redis)"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.l1_cache = cachetools.TTLCache(maxsize=1000, ttl=60)  # 1 min L1
        
    async def get(self, key: str) -> Optional[Any]:
        """Get from L1, then L2"""
        # Try L1 cache first
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # Try L2 (Redis)
        value = await self.redis.get(key)
        if value:
            deserialized = pickle.loads(value)
            self.l1_cache[key] = deserialized  # Populate L1
            return deserialized
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set in both L1 and L2"""
        self.l1_cache[key] = value
        serialized = pickle.dumps(value)
        await self.redis.setex(key, ttl, serialized)
    
    async def delete(self, key: str):
        """Delete from both levels"""
        self.l1_cache.pop(key, None)
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern"""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(
                str(args).encode() + str(kwargs).encode()
            ).hexdigest()}"
            
            cache_manager = kwargs.get('cache_manager')
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # Try cache first
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator