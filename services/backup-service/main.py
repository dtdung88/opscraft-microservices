from fastapi import FastAPI, BackgroundTasks, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import subprocess
import boto3
import logging
import os

from config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()


class BackupManager:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = settings.BACKUP_BUCKET

    def _init_s3(self):
        if self.s3_client is None:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

    async def backup_database(self, db_name: str, db_host: str, db_user: str, db_password: str):
        """Backup PostgreSQL database"""
        self._init_s3()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"/tmp/{db_name}_backup_{timestamp}.sql"

        try:
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-U', db_user,
                '-d', db_name,
                '-F', 'c',
                '-f', backup_file
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            subprocess.run(cmd, env=env, check=True)

            s3_key = f"databases/{db_name}/{timestamp}/{db_name}.sql"
            self.s3_client.upload_file(backup_file, self.bucket_name, s3_key)

            logger.info(f"Database backup completed: {s3_key}")
            os.remove(backup_file)

            await self.cleanup_old_backups(f"databases/{db_name}", days=settings.RETENTION_DAYS)

            return {"status": "success", "file": s3_key}

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def backup_scripts(self):
        """Backup all scripts from Script Service"""
        import httpx
        self._init_s3()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://script-service:8002/api/v1/scripts/export",
                    timeout=60.0
                )

                if response.status_code == 200:
                    backup_file = f"/tmp/scripts_backup_{timestamp}.json"

                    with open(backup_file, 'wb') as f:
                        f.write(response.content)

                    s3_key = f"scripts/{timestamp}/scripts.json"
                    self.s3_client.upload_file(backup_file, self.bucket_name, s3_key)

                    logger.info(f"Scripts backup completed: {s3_key}")
                    os.remove(backup_file)

                    await self.cleanup_old_backups("scripts", days=settings.RETENTION_DAYS)

                    return {"status": "success", "file": s3_key}

            return {"status": "failed", "error": "Script service unavailable"}

        except Exception as e:
            logger.error(f"Scripts backup failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def cleanup_old_backups(self, prefix: str, days: int):
        """Delete backups older than specified days"""
        self._init_s3()
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        logger.info(f"Deleted old backup: {obj['Key']}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    async def restore_database(self, backup_file: str, db_name: str):
        """Restore database from backup"""
        self._init_s3()
        try:
            local_file = f"/tmp/restore_{db_name}.sql"
            self.s3_client.download_file(self.bucket_name, backup_file, local_file)

            cmd = [
                'pg_restore',
                '-h', os.getenv('DB_HOST', 'localhost'),
                '-U', os.getenv('DB_USER', 'postgres'),
                '-d', db_name,
                '-c',
                local_file
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD', '')

            subprocess.run(cmd, env=env, check=True)

            logger.info(f"Database restored: {db_name}")
            os.remove(local_file)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {"status": "failed", "error": str(e)}


backup_manager = BackupManager()
scheduler = AsyncIOScheduler()


async def scheduled_backup():
    logger.info("Starting scheduled backup...")
    await backup_manager.backup_scripts()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    scheduler.add_job(
        scheduled_backup,
        CronTrigger.from_crontab(settings.BACKUP_CRON),
        id="daily_backup"
    )
    scheduler.start()
    yield
    scheduler.shutdown()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.post("/api/v1/backup/database/{db_name}")
async def backup_database(db_name: str, background_tasks: BackgroundTasks):
    """Trigger database backup"""
    db_configs = {
        "auth": settings.AUTH_DB_URL,
        "script": settings.SCRIPT_DB_URL,
        "execution": settings.EXECUTION_DB_URL,
        "secret": settings.SECRET_DB_URL,
    }

    if db_name not in db_configs:
        raise HTTPException(status_code=404, detail="Database not found")

    background_tasks.add_task(
        backup_manager.backup_database,
        db_name,
        "localhost",
        "postgres",
        "postgres"
    )
    return {"message": f"Backup started for {db_name}"}


@app.post("/api/v1/backup/scripts")
async def backup_scripts(background_tasks: BackgroundTasks):
    """Trigger scripts backup"""
    background_tasks.add_task(backup_manager.backup_scripts)
    return {"message": "Scripts backup started"}