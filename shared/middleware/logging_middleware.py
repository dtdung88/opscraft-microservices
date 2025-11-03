from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Get correlation ID
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration
            }
        )
        
        return response