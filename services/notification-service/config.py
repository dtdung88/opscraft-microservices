from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    SERVICE_NAME: str = "notification-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8005
    
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    
    # Email configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # Slack configuration
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_BOT_TOKEN: Optional[str] = None
    
    # Teams configuration
    TEAMS_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()