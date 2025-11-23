"""Centralized error handling for all services"""
import logging
from typing import Any, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import HTTPError, TimeoutException
from kafka.errors import KafkaError
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.exceptions.custom_exceptions import (
    OpsCraftException,
    exception_to_http_status,
)

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def create(
        error_code: str,
        message: str,
        status_code: int,
        details: dict = None,
        request_id: str = None,
    ) -> dict:
        """Create standardized error response"""
        response = {
            "success": False,
            "error": {"code": error_code, "message": message, "status": status_code},
        }

        if details:
            response["error"]["details"] = details

        if request_id:
            response["request_id"] = request_id

        return response


async def opscraft_exception_handler(
    request: Request, exc: OpsCraftException
) -> JSONResponse:
    """Handle custom OpsCraft exceptions"""
    request_id = getattr(request.state, "correlation_id", None)

    logger.warning(
        f"OpsCraft exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "request_id": request_id,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exception_to_http_status(exc),
        content=ErrorResponse.create(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exception_to_http_status(exc),
            details=exc.details,
            request_id=request_id,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = getattr(request.state, "correlation_id", None)

    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"errors": errors, "request_id": request_id},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": errors},
            request_id=request_id,
        ),
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle database errors"""
    request_id = getattr(request.state, "correlation_id", None)

    # Don't expose internal database errors in production
    if isinstance(exc, IntegrityError):
        error_code = "INTEGRITY_ERROR"
        message = "Database constraint violation"
        status_code = status.HTTP_409_CONFLICT
    else:
        error_code = "DATABASE_ERROR"
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        f"Database error: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse.create(
            error_code=error_code,
            message=message,
            status_code=status_code,
            request_id=request_id,
        ),
    )


async def redis_exception_handler(request: Request, exc: RedisError) -> JSONResponse:
    """Handle Redis errors"""
    request_id = getattr(request.state, "correlation_id", None)

    logger.error(f"Redis error: {exc}", extra={"request_id": request_id}, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse.create(
            error_code="CACHE_ERROR",
            message="Cache service temporarily unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id=request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPError) -> JSONResponse:
    """Handle HTTP client errors"""
    request_id = getattr(request.state, "correlation_id", None)

    if isinstance(exc, TimeoutException):
        error_code = "SERVICE_TIMEOUT"
        message = "External service request timed out"
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    else:
        error_code = "EXTERNAL_SERVICE_ERROR"
        message = "External service request failed"
        status_code = status.HTTP_502_BAD_GATEWAY

    logger.error(
        f"HTTP client error: {exc}", extra={"request_id": request_id}, exc_info=True
    )

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse.create(
            error_code=error_code,
            message=message,
            status_code=status_code,
            request_id=request_id,
        ),
    )


async def kafka_exception_handler(request: Request, exc: KafkaError) -> JSONResponse:
    """Handle Kafka errors"""
    request_id = getattr(request.state, "correlation_id", None)

    logger.error(f"Kafka error: {exc}", extra={"request_id": request_id}, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse.create(
            error_code="MESSAGE_QUEUE_ERROR",
            message="Message queue temporarily unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, "correlation_id", None)

    logger.exception(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with FastAPI app"""

    # Custom exceptions
    app.add_exception_handler(OpsCraftException, opscraft_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Infrastructure errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    app.add_exception_handler(HTTPError, http_exception_handler)
    app.add_exception_handler(KafkaError, kafka_exception_handler)

    # Catch-all
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")


# Decorator for safe async operations
def safe_async(default_return: Any = None):
    """Decorator to safely execute async functions with error handling"""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except OpsCraftException:
                raise  # Re-raise custom exceptions
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator
