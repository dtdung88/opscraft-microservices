from fastapi import Request
import uuid
import logging

logger = logging.getLogger(__name__)

class CorrelationMiddleware:
    async def __call__(self, request: Request, call_next):
        # Get or create correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add to logger context
        logger = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {"correlation_id": correlation_id}
        )
        request.state.logger = logger
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response