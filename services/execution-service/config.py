from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SERVICE_NAME: str = "execution-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8003
    
    DATABASE_URL: str
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    SCRIPT_SERVICE_URL: str = "http://script-service:8002"
    SECRET_SERVICE_URL: str = "http://secret-service:8004"
    
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    DOCKER_ENABLED: bool = True
    MAX_CONCURRENT_EXECUTIONS: int = 10
    EXECUTION_TIMEOUT_SECONDS: int = 3600
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()