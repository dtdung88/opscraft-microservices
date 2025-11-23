"""Role-Based Access Control implementation."""
from enum import Enum
from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException, Request, status


class Role(str, Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Available permissions in the system."""

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Script management
    SCRIPT_CREATE = "script:create"
    SCRIPT_READ = "script:read"
    SCRIPT_UPDATE = "script:update"
    SCRIPT_DELETE = "script:delete"
    SCRIPT_EXECUTE = "script:execute"

    # Secret management
    SECRET_CREATE = "secret:create"
    SECRET_READ = "secret:read"
    SECRET_UPDATE = "secret:update"
    SECRET_DELETE = "secret:delete"
    SECRET_REVEAL = "secret:reveal"

    # Execution management
    EXECUTION_CREATE = "execution:create"
    EXECUTION_READ = "execution:read"
    EXECUTION_CANCEL = "execution:cancel"

    # Admin operations
    ADMIN_ACCESS = "admin:access"
    AUDIT_READ = "audit:read"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: {
        Permission.SCRIPT_READ,
        Permission.EXECUTION_READ,
        Permission.USER_READ,
    },
    Role.OPERATOR: {
        Permission.SCRIPT_READ,
        Permission.SCRIPT_CREATE,
        Permission.SCRIPT_UPDATE,
        Permission.SCRIPT_EXECUTE,
        Permission.EXECUTION_READ,
        Permission.EXECUTION_CREATE,
        Permission.EXECUTION_CANCEL,
        Permission.SECRET_READ,
        Permission.USER_READ,
    },
    Role.ADMIN: set(Permission),  # Admin has all permissions
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if role has specified permission."""
    try:
        user_role = Role(role)
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    except ValueError:
        return False


def get_role_level(role: str) -> int:
    """Get numeric level for role comparison."""
    levels = {Role.VIEWER: 1, Role.OPERATOR: 2, Role.ADMIN: 3}
    try:
        return levels.get(Role(role), 0)
    except ValueError:
        return 0


def require_permission(permission: Permission) -> Callable:
    """Decorator to require specific permission."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_role = request.state.user.get("role", "")
            if not has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(minimum_role: Role) -> Callable:
    """Decorator to require minimum role level."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_role = request.state.user.get("role", "")
            if get_role_level(user_role) < get_role_level(minimum_role.value):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Minimum role required: {minimum_role.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator