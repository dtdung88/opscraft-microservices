from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import boto3
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backup Service")
scheduler = AsyncIOScheduler()

class BackupManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('BACKUP_BUCKET', 'opscraft-backups')
    
    async def backup_database(self, db_name: str, db_host: str, db_user: str, db_password: str):
        """Backup PostgreSQL database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"/tmp/{db_name}_backup_{timestamp}.sql"
        
        try:
            # Create backup using pg_dump
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
            
            # Upload to S3
            s3_key = f"databases/{db_name}/{timestamp}/{db_name}.sql"
            
            self.s3_client.upload_file(
                backup_file,
                self.bucket_name,
                s3_key
            )
            
            logger.info(f"Database backup completed: {s3_key}")
            
            # Clean up local file
            os.remove(backup_file)
            
            # Delete old backups (keep last 30 days)
            await self.cleanup_old_backups(f"databases/{db_name}", days=30)
            
            return {"status": "success", "file": s3_key}
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def backup_scripts(self):
        """Backup all scripts from Script Service"""
        import httpx
        
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
                    
                    # Upload to S3
                    s3_key = f"scripts/{timestamp}/scripts.json"
                    
                    self.s3_client.upload_file(
                        backup_file,
                        self.bucket_name,
                        s3_key
                    )
                    
                    logger.info(f"Scripts backup completed: {s3_key}")
                    
                    os.remove(backup_file)
                    
                    await self.cleanup_old_backups("scripts", days=30)
                    
                    return {"status": "success", "file": s3_key}
        
        except Exception as e:
            logger.error(f"Scripts backup failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def cleanup_old_backups(self, prefix: str, days: int):
        """Delete backups older than specified days"""
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
        try:
            # Download from S3
            local_file = f"/tmp/restore_{db_name}.sql"
            
            self.s3_client.download_file(
                self.bucket_name,
                backup_file,
                local_file
            )
            
            # Restore using pg_restore
            cmd = [
                'pg_restore',
                '-h', os.getenv('DB_HOST'),
                '-U', os.getenv('DB_USER'),
                '-d', db_name,
                '-c',  # Clean (drop) database objects before creating
                local_file
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD')
            
            subprocess.run(cmd, env=env, check=True)
            
            logger.info(f"Database restored: {db_name}")
            
            os.remove(local_file)
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {"status": "failed", "error": str(e)}

backup_manager = BackupManager()

# Schedule daily backups at 2 AM
@scheduler.scheduled_job(CronTrigger(hour=2, minute=0))
async def scheduled_backup():
    logger.info("Starting scheduled backup...")
    