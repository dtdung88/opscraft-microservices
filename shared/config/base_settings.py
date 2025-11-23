"""Base configuration with validation for all services"""
import logging
from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection URL",
        pattern=r"^postgresql(\+\w+)?://.*",
    )
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_PRE_PING: bool = Field(default=True)
    DB_ECHO: bool = Field(default=False)

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


class RedisSettings(BaseSettings):
    """Redis configuration"""

    REDIS_URL: str = Field(
        ..., description="Redis connection URL", pattern=r"^redis://.*"
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1, le=1000)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


class KafkaSettings(BaseSettings):
    """Kafka configuration"""

    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="kafka:9092", description="Kafka bootstrap servers"
    )
    KAFKA_CLIENT_ID: Optional[str] = None
    KAFKA_COMPRESSION_TYPE: str = Field(default="gzip")
    KAFKA_ACKS: str = Field(default="all")
    KAFKA_RETRIES: int = Field(default=3, ge=0, le=10)

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


class SecuritySettings(BaseSettings):
    """Security configuration"""

    SECRET_KEY: str = Field(
        ..., min_length=32, description="Secret key for JWT signing"
    )
    ENCRYPTION_KEY: str = Field(
        ..., min_length=32, description="Encryption key for sensitive data"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # Password policy
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=8)
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True)
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True)

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @field_validator("SECRET_KEY", "ENCRYPTION_KEY")
    @classmethod
    def validate_key_strength(cls, v: str) -> str:
        """Ensure keys are strong enough"""
        if len(v) < 32:
            raise ValueError("Key must be at least 32 characters")
        return v


class ServiceSettings(BaseSettings):
    """Common service configuration"""

    SERVICE_NAME: str = Field(..., min_length=1)
    SERVICE_VERSION: str = Field(default="1.0.0")
    SERVICE_PORT: int = Field(..., ge=1024, le=65535)

    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    # Timeouts
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=300)

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = {"development", "staging", "production", "test"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()


class BaseServiceSettings(BaseSettings):
    """Complete base configuration combining all settings"""

    # Service info
    service: ServiceSettings

    # Infrastructure
    database: DatabaseSettings
    redis: RedisSettings
    kafka: KafkaSettings
    security: SecuritySettings

    # Service URLs (optional)
    AUTH_SERVICE_URL: str = Field(default="http://auth-service:8001")
    SCRIPT_SERVICE_URL: str = Field(default="http://script-service:8002")
    EXECUTION_SERVICE_URL: str = Field(default="http://execution-service:8003")
    SECRET_SERVICE_URL: str = Field(default="http://secret-service:8004")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification-service:8005")

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @classmethod
    def load(cls, service_name: str, service_port: int) -> "BaseServiceSettings":
        """Load configuration with defaults"""
        try:
            return cls(
                service=ServiceSettings(
                    SERVICE_NAME=service_name, SERVICE_PORT=service_port
                ),
                database=DatabaseSettings(),
                redis=RedisSettings(),
                kafka=KafkaSettings(),
                security=SecuritySettings(),
            )
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.service.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.service.ENVIRONMENT == "development"


# Validation on import
def validate_required_env_vars() -> None:
    """Validate critical environment variables on startup"""
    required = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL", "ENCRYPTION_KEY"]

    import os

    missing = [var for var in required if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in .env file or environment"
        )
