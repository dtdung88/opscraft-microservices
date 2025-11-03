from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SERVICE_NAME: str = "notification-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8005
    
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()