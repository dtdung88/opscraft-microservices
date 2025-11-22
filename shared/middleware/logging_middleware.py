from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "N/A")

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
            }
        )

        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

        return response