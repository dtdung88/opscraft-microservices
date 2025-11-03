from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SERVICE_NAME: str = "admin-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8006
    
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    SCRIPT_SERVICE_URL: str = "http://script-service:8002"
    EXECUTION_SERVICE_URL: str = "http://execution-service:8003"
    SECRET_SERVICE_URL: str = "http://secret-service:8004"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()