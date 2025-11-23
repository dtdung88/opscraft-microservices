"""JWT token management utilities."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from config import settings


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str
    user_id: int
    role: str
    type: str
    exp: datetime
    iat: datetime
    jti: Optional[str] = None


def create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT token with specified type and expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    elif token_type == "access":
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": token_type,
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.debug(f"Token decode failed: {e}")
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[TokenPayload]:
    """Verify token is of expected type."""
    payload = decode_token(token)
    if payload and payload.type == expected_type:
        return payload
    return None


import logging

logger = logging.getLogger(__name__)