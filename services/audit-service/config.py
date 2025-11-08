from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "audit-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8009
    
    DATABASE_URL: str
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    RETENTION_DAYS: int = 365
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()