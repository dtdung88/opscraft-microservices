from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest,
    Token, PasswordChangeRequest
)
from app.services.auth_service import AuthService
from app.core.security import get_current_user
from app.core.event import event_publisher

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)

    if auth_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if auth_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = auth_service.create_user(user_data)

    await event_publisher.publish(
        "user-events",
        {
            "event_type": "user.created",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    return user


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login and get JWT tokens"""
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(
        credentials.username,
        credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    tokens = auth_service.create_tokens(user)

    await event_publisher.publish(
        "user-events",
        {
            "event_type": "user.logged_in",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    return auth_service.refresh_access_token(refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    auth_service.change_password(
        current_user,
        password_data.old_password,
        password_data.new_password
    )
    return {"message": "Password changed successfully"}


@router.post("/verify-token")
async def verify_token(token: str, db: Session = Depends(get_db)):
    """Verify JWT token (for other services)"""
    auth_service = AuthService(db)
    try:
        user = auth_service.verify_token(token)
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}