"""Shared security dependencies"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.security.auth import decode_token

security = HTTPBearer()

async def get_current_user_data(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract user data from JWT token"""
    token = credentials.credentials
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    role: str = payload.get("role")
    
    if username is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {"user_id": user_id, "username": username, "role": role}

async def require_role(required_role: str, user_data: dict = Depends(get_current_user_data)):
    """Check if user has required role"""
    role_hierarchy = {"viewer": 1, "operator": 2, "admin": 3}
    user_role_level = role_hierarchy.get(user_data["role"], 0)
    required_level = role_hierarchy.get(required_role, 999)
    
    if user_role_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires {required_role} role or higher"
        )
    return user_data
