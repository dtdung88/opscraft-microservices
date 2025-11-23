"""Advanced rate limiting with Redis"""
import hashlib
import logging
import time
from enum import Enum
from functools import wraps
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": retry_after,
                "message": f"Too many requests. Please try again in {retry_after} seconds.",
            },
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """Advanced Redis-based rate limiter"""

    def __init__(
        self,
        redis_url: str,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.strategy = strategy

    async def check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit for a key

        Returns:
            (allowed, remaining, retry_after)
        """
        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window(key, limit, window)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window(key, limit, window)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket(key, limit, window)
        else:
            return await self._sliding_window(key, limit, window)

    async def _fixed_window(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """Fixed window rate limiting"""
        current = int(time.time())
        window_key = f"rate_limit:{key}:{current // window}"

        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window)
        results = await pipe.execute()

        count = results[0]
        remaining = max(0, limit - count)
        allowed = count <= limit
        retry_after = window if not allowed else 0

        return allowed, remaining, retry_after

    async def _sliding_window(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """Sliding window rate limiting (most accurate)"""
        now = time.time()
        window_start = now - window

        rate_key = f"rate_limit:sliding:{key}"

        # Remove old entries and add current request
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(rate_key, 0, window_start)
        pipe.zadd(rate_key, {str(now): now})
        pipe.zcount(rate_key, window_start, now)
        pipe.expire(rate_key, window)
        results = await pipe.execute()

        count = results[2]
        remaining = max(0, limit - count)
        allowed = count <= limit

        # Calculate retry_after
        if not allowed:
            # Get oldest request in window
            oldest = await self.redis.zrange(rate_key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(oldest_time + window - now)
            else:
                retry_after = window
        else:
            retry_after = 0

        return allowed, remaining, retry_after

    async def _token_bucket(
        self, key: str, capacity: int, refill_rate: int
    ) -> tuple[bool, int, int]:
        """Token bucket rate limiting"""
        bucket_key = f"rate_limit:bucket:{key}"

        # Get current state
        bucket_data = await self.redis.hgetall(bucket_key)

        now = time.time()
        tokens = float(bucket_data.get("tokens", capacity))
        last_refill = float(bucket_data.get("last_refill", now))

        # Calculate tokens to add
        time_passed = now - last_refill
        tokens_to_add = time_passed * refill_rate
        tokens = min(capacity, tokens + tokens_to_add)

        # Try to consume a token
        if tokens >= 1:
            tokens -= 1
            allowed = True
            retry_after = 0
        else:
            allowed = False
            retry_after = int((1 - tokens) / refill_rate)

        # Update state
        await self.redis.hset(
            bucket_key, mapping={"tokens": tokens, "last_refill": now}
        )
        await self.redis.expire(bucket_key, 3600)

        remaining = int(tokens)
        return allowed, remaining, retry_after

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        pattern = f"rate_limit:*:{key}"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def get_usage(self, key: str) -> dict:
        """Get current usage statistics"""
        pattern = f"rate_limit:*:{key}"
        keys = await self.redis.keys(pattern)

        total_requests = 0
        for k in keys:
            if "sliding" in k:
                total_requests = await self.redis.zcard(k)
            else:
                total_requests += int(await self.redis.get(k) or 0)

        return {
            "key": key,
            "total_requests": total_requests,
            "active_windows": len(keys),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(
        self,
        app,
        redis_url: str,
        default_limit: int = 60,
        default_window: int = 60,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(redis_url, strategy)
        self.default_limit = default_limit
        self.default_window = default_window

        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/v1/auth/login": (5, 300),  # 5 per 5 minutes
            "/api/v1/auth/register": (3, 3600),  # 3 per hour
            "/api/v1/executions": (20, 60),  # 20 per minute
        }

    def _get_client_key(self, request: Request) -> str:
        """Generate unique client identifier"""
        # Try to get user from request state
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("user_id")
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _get_limits(self, path: str) -> tuple[int, int]:
        """Get rate limits for endpoint"""
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        return self.default_limit, self.default_window

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        client_key = self._get_client_key(request)
        endpoint = request.url.path
        limit, window = self._get_limits(endpoint)

        # Create rate limit key
        rate_key = f"{client_key}:{endpoint}"

        try:
            allowed, remaining, retry_after = await self.limiter.check_rate_limit(
                rate_key, limit, window
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {client_key} on {endpoint}",
                    extra={
                        "client_key": client_key,
                        "endpoint": endpoint,
                        "retry_after": retry_after,
                    },
                )
                raise RateLimitExceeded(retry_after)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

            return response

        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            # Continue without rate limiting on errors
            return await call_next(request)


def rate_limit(limit: int = 10, window: int = 60):
    """
    Decorator for endpoint-specific rate limiting

    Usage:
        @app.get("/api/endpoint")
        @rate_limit(limit=5, window=60)
        async def endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args or kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            # Get rate limiter from app state
            if hasattr(request.app.state, "rate_limiter"):
                limiter = request.app.state.rate_limiter

                # Generate key
                client_key = f"ip:{request.client.host}"
                if hasattr(request.state, "user"):
                    user_id = request.state.user.get("user_id")
                    if user_id:
                        client_key = f"user:{user_id}"

                endpoint = request.url.path
                rate_key = f"{client_key}:{endpoint}:{func.__name__}"

                # Check rate limit
                allowed, remaining, retry_after = await limiter.check_rate_limit(
                    rate_key, limit, window
                )

                if not allowed:
                    raise RateLimitExceeded(retry_after)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# IP-based rate limiter for authentication endpoints
class AuthRateLimiter:
    """Specialized rate limiter for authentication"""

    def __init__(self, redis_url: str):
        self.limiter = RateLimiter(redis_url)

        # Progressive delays for failed attempts
        self.failed_attempt_delays = {
            3: 60,  # 1 minute
            5: 300,  # 5 minutes
            10: 900,  # 15 minutes
            20: 3600,  # 1 hour
        }

    async def check_auth_attempt(
        self, identifier: str, success: bool
    ) -> tuple[bool, int]:
        """
        Check if authentication attempt is allowed

        Returns:
            (allowed, retry_after)
        """
        key = f"auth_attempts:{identifier}"

        if success:
            # Reset on successful auth
            await self.limiter.redis.delete(key)
            return True, 0

        # Increment failed attempts
        attempts = await self.limiter.redis.incr(key)
        await self.limiter.redis.expire(key, 3600)  # 1 hour expiry

        # Check if account should be locked
        for threshold, delay in sorted(self.failed_attempt_delays.items()):
            if attempts >= threshold:
                return False, delay

        return True, 0

    async def get_failed_attempts(self, identifier: str) -> int:
        """Get number of failed attempts"""
        key = f"auth_attempts:{identifier}"
        attempts = await self.limiter.redis.get(key)
        return int(attempts) if attempts else 0
