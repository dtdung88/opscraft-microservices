"""Centralized secrets management with validation"""
import base64
import logging
import os
import secrets as py_secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)


class SecretsManager:
    """Centralized secrets manager with validation"""

    _instance: Optional["SecretsManager"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._validate_environment()
            self._encryption_key = self._get_or_generate_key()
            self._fernet = Fernet(self._encryption_key)
            self.__class__._initialized = True

    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
        ]

        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # Validate secret key strength
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from environment or generate"""
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            logger.warning(
                "ENCRYPTION_KEY not set, generating temporary key. "
                "This should NOT be used in production!"
            )
            encryption_key = py_secrets.token_hex(32)

        # Derive Fernet key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"opscraft_v1",  # Use per-installation salt in production
            iterations=100000,
            backend=default_backend(),
        )

        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")

        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def generate_token(nbytes: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return py_secrets.token_urlsafe(nbytes)

    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """Get secret from environment with validation"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Secret '{key}' not found in environment")
        return value

    @staticmethod
    def mask_secret(secret: str, visible_chars: int = 4) -> str:
        """Mask secret for logging"""
        if len(secret) <= visible_chars:
            return "*" * len(secret)
        return secret[:visible_chars] + "*" * (len(secret) - visible_chars)


# Global instance
secrets_manager = SecretsManager()
