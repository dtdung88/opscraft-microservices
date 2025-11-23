from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from shared.exceptions.custom_exceptions import (
    AuthenticationError,
    ResourceAlreadyExistsError,
    ValidationError,
)
from shared.security.secrets import secrets_manager
from shared.services.base_service import AuditedService
from shared.validation.validators import InputValidator


class UserService(AuditedService):
    """User management service"""

    def __init__(self, db: Session):
        super().__init__(db, User, "user")

    def _validate_create(self, data: dict) -> None:
        """Validate user creation"""
        # Validate username
        username_result = InputValidator.validate_username(data.get("username", ""))
        if not username_result:
            raise ValidationError(
                "Invalid username",
                [{"field": "username", "message": username_result.message}],
            )

        # Validate email
        email_result = InputValidator.validate_email(data.get("email", ""))
        if not email_result:
            raise ValidationError(
                "Invalid email", [{"field": "email", "message": email_result.message}]
            )

        # Validate password
        password_result = InputValidator.validate_password(data.get("password", ""))
        if not password_result:
            raise ValidationError(
                "Weak password",
                [{"field": "password", "errors": password_result.errors}],
            )

        # Check for existing username
        if self.exists(username=data["username"]):
            raise ResourceAlreadyExistsError("user", data["username"])

        # Check for existing email
        if self.exists(email=data["email"]):
            raise ResourceAlreadyExistsError("user", data["email"])

    def create_user(self, user_data: UserCreate, auto_admin: bool = False) -> User:
        """Create new user with password hashing"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Hash password
        hashed_password = pwd_context.hash(user_data.password)

        # Determine role
        is_first_user = self.count() == 0
        role = UserRole.ADMIN if (is_first_user or auto_admin) else UserRole.VIEWER

        # Create user
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["role"] = role

        return self.create(user_dict)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = (
            self.db.query(User)
            .filter(User.username == username, User.is_active == True)
            .first()
        )

        if not user:
            return None

        if not pwd_context.verify(password, user.hashed_password):
            return None

        return user

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = self.get_or_404(user_id)

        # Verify old password
        if not pwd_context.verify(old_password, user.hashed_password):
            raise AuthenticationError("Incorrect password")

        # Validate new password
        password_result = InputValidator.validate_password(new_password)
        if not password_result:
            raise ValidationError(
                "Weak password",
                [{"field": "password", "errors": password_result.errors}],
            )

        # Update password
        user.hashed_password = pwd_context.hash(new_password)
        self.db.commit()

        return True
