"""Custom exceptions for OpsCraft microservices."""
from typing import Any, Optional


class OpsCraftException(Exception):
    """Base exception for OpsCraft services."""

    def __init__(
        self,
        message: str,
        error_code: str = "OPSCRAFT_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# Authentication & Authorization Exceptions
# ============================================================================
class AuthenticationError(OpsCraftException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTH_FAILED", details)


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)
        self.error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)
        self.error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN"


class AuthorizationError(OpsCraftException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_role: Optional[str] = None,
    ):
        details = {"required_role": required_role} if required_role else {}
        super().__init__(message, "AUTHORIZATION_FAILED", details)


# ============================================================================
# Resource Exceptions
# ============================================================================
class ResourceNotFoundError(OpsCraftException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        message: Optional[str] = None,
    ):
        msg = message or f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            msg,
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": str(resource_id)},
        )


class ResourceAlreadyExistsError(OpsCraftException):
    """Raised when trying to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None,
    ):
        msg = message or f"{resource_type} '{identifier}' already exists"
        super().__init__(
            msg,
            "RESOURCE_EXISTS",
            {"resource_type": resource_type, "identifier": identifier},
        )


class ResourceConflictError(OpsCraftException):
    """Raised when there's a conflict with the resource state."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = str(resource_id)
        super().__init__(message, "RESOURCE_CONFLICT", details)


# ============================================================================
# Validation Exceptions
# ============================================================================
class ValidationError(OpsCraftException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", {"errors": errors or []})


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, field: str, message: str):
        super().__init__(
            f"Invalid input for field '{field}': {message}",
            [{"field": field, "message": message}],
        )


class ScriptValidationError(ValidationError):
    """Raised when script content validation fails."""

    def __init__(
        self,
        message: str = "Script validation failed",
        errors: Optional[list[str]] = None,
    ):
        error_details = [{"message": e} for e in (errors or [])]
        super().__init__(message, error_details)
        self.error_code = "SCRIPT_VALIDATION_ERROR"


# ============================================================================
# Execution Exceptions
# ============================================================================
class ExecutionError(OpsCraftException):
    """Raised when script execution fails."""

    def __init__(
        self,
        message: str,
        execution_id: Optional[int] = None,
        exit_code: Optional[int] = None,
    ):
        details = {}
        if execution_id:
            details["execution_id"] = execution_id
        if exit_code is not None:
            details["exit_code"] = exit_code
        super().__init__(message, "EXECUTION_ERROR", details)


class ExecutionTimeoutError(ExecutionError):
    """Raised when execution times out."""

    def __init__(
        self,
        execution_id: int,
        timeout_seconds: int,
    ):
        super().__init__(
            f"Execution {execution_id} timed out after {timeout_seconds} seconds",
            execution_id,
        )
        self.error_code = "EXECUTION_TIMEOUT"
        self.details["timeout_seconds"] = timeout_seconds


class ExecutionCancelledError(ExecutionError):
    """Raised when execution is cancelled."""

    def __init__(self, execution_id: int, cancelled_by: str):
        super().__init__(
            f"Execution {execution_id} was cancelled",
            execution_id,
        )
        self.error_code = "EXECUTION_CANCELLED"
        self.details["cancelled_by"] = cancelled_by


# ============================================================================
# Service Communication Exceptions
# ============================================================================
class ServiceUnavailableError(OpsCraftException):
    """Raised when a service is unavailable."""

    def __init__(self, service_name: str, message: Optional[str] = None):
        msg = message or f"Service '{service_name}' is unavailable"
        super().__init__(msg, "SERVICE_UNAVAILABLE", {"service": service_name})


class ServiceTimeoutError(ServiceUnavailableError):
    """Raised when a service request times out."""

    def __init__(self, service_name: str, timeout_seconds: float):
        super().__init__(
            service_name,
            f"Request to '{service_name}' timed out after {timeout_seconds}s",
        )
        self.error_code = "SERVICE_TIMEOUT"
        self.details["timeout_seconds"] = timeout_seconds


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================
class RateLimitExceededError(OpsCraftException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


# ============================================================================
# Secret Management Exceptions
# ============================================================================
class SecretAccessError(OpsCraftException):
    """Raised when secret access fails."""

    def __init__(self, secret_name: str, message: Optional[str] = None):
        msg = message or f"Cannot access secret '{secret_name}'"
        super().__init__(msg, "SECRET_ACCESS_ERROR", {"secret_name": secret_name})


class EncryptionError(OpsCraftException):
    """Raised when encryption/decryption fails."""

    def __init__(self, operation: str, message: Optional[str] = None):
        msg = message or f"Encryption operation '{operation}' failed"
        super().__init__(msg, "ENCRYPTION_ERROR", {"operation": operation})


# ============================================================================
# Exception Handler Helper
# ============================================================================
def exception_to_http_status(exc: OpsCraftException) -> int:
    """Map exception to HTTP status code."""
    status_map = {
        "AUTH_FAILED": 401,
        "INVALID_CREDENTIALS": 401,
        "TOKEN_EXPIRED": 401,
        "INVALID_TOKEN": 401,
        "AUTHORIZATION_FAILED": 403,
        "RESOURCE_NOT_FOUND": 404,
        "RESOURCE_EXISTS": 409,
        "RESOURCE_CONFLICT": 409,
        "VALIDATION_ERROR": 400,
        "SCRIPT_VALIDATION_ERROR": 400,
        "EXECUTION_ERROR": 500,
        "EXECUTION_TIMEOUT": 504,
        "EXECUTION_CANCELLED": 499,
        "SERVICE_UNAVAILABLE": 503,
        "SERVICE_TIMEOUT": 504,
        "RATE_LIMIT_EXCEEDED": 429,
        "SECRET_ACCESS_ERROR": 403,
        "ENCRYPTION_ERROR": 500,
    }
    return status_map.get(exc.error_code, 500)