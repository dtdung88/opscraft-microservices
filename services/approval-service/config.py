from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SERVICE_NAME: str = "approval-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8008
    
    DATABASE_URL: str
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    
    DEFAULT_APPROVAL_EXPIRY_HOURS: int = 72
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()