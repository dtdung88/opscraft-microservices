from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SERVICE_NAME: str = "backup-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8010

    # Database connections
    AUTH_DB_URL: str = "postgresql://postgres:postgres@auth-db:5432/auth_db"
    SCRIPT_DB_URL: str = "postgresql://postgres:postgres@script-db:5432/script_db"
    EXECUTION_DB_URL: str = "postgresql://postgres:postgres@execution-db:5432/execution_db"
    SECRET_DB_URL: str = "postgresql://postgres:postgres@secret-db:5432/secret_db"

    # S3/Object Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    BACKUP_BUCKET: str = "opscraft-backups"

    # Backup schedule
    BACKUP_CRON: str = "0 2 * * *"  # 2 AM daily
    RETENTION_DAYS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True