from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, Token
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        # First user is admin, others are viewers
        is_first_user = self.db.query(User).count() == 0
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=UserRole.ADMIN if is_first_user else UserRole.VIEWER,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_tokens(self, user: User) -> Token:
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        user = self.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return self.create_tokens(user)
    
    def change_password(self, user: User, old_password: str, new_password: str):
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
    
    def verify_token(self, token: str) -> User:
        payload = decode_token(token)
        
        if payload is None or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = payload.get("user_id")
        user = self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user