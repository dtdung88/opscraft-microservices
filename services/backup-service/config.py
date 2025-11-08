from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "backup-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8010
    
    # Database connections
    AUTH_DB_URL: str
    SCRIPT_DB_URL: str
    EXECUTION_DB_URL: str
    SECRET_DB_URL: str
    
    # S3/Object Storage
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    BACKUP_BUCKET: str = "opscraft-backups"
    
    # Backup schedule
    BACKUP_CRON: str = "0 2 * * *"  # 2 AM daily
    RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True