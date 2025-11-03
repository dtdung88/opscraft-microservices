from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Service Info
    SERVICE_NAME: str = "auth-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 3600
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_USER_EVENTS: str = "user-events"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Tracing
    JAEGER_HOST: str = "jaeger"
    JAEGER_PORT: int = 6831
    
    # Service Discovery
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()