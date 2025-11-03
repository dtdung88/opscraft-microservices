from celery import Celery
import docker
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from config import settings
from app.db.session import SessionLocal
from app.models.execution import Execution, ExecutionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    'execution_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(name='execute_script')
def execute_script_task(execution_id: int):
    db = SessionLocal()
    
    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        # Update status to running
        execution.status = ExecutionStatus.RUNNING
        db.commit()
        
        # Execute script in Docker
        client = docker.from_env()
        
        # Determine image based on script type
        image_map = {
            "bash": "bash:latest",
            "python": "python:3.12-slim",
            "ansible": "ansible/ansible:latest",
            "terraform": "hashicorp/terraform:latest"
        }
        
        script_type = execution.parameters.get("script_type", "bash")
        image = image_map.get(script_type, "bash:latest")
        
        # Run container
        container = client.containers.run(
            image,
            command=["sh", "-c", execution.parameters.get("content", "echo 'No content'")],
            detach=True,
            remove=True,
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=50000
        )
        
        # Stream logs
        logs = container.logs(stream=True, follow=True)
        output_lines = []
        
        for log in logs:
            line = log.decode('utf-8')
            output_lines.append(line)
            logger.info(f"Execution {execution_id}: {line}")
        
        # Wait for completion
        result = container.wait()
        exit_code = result['StatusCode']
        
        # Update execution
        execution.output = ''.join(output_lines)
        execution.status = ExecutionStatus.SUCCESS if exit_code == 0 else ExecutionStatus.FAILED
        execution.completed_at = datetime.now(timezone.utc)
        
        if exit_code != 0:
            execution.error = f"Exit code: {exit_code}"
        
        db.commit()
        
        logger.info(f"Execution {execution_id} completed with status {execution.status}")
        
    except Exception as e:
        logger.error(f"Execution {execution_id} failed: {e}")
        execution.status = ExecutionStatus.FAILED
        execution.error = str(e)
        execution.completed_at = datetime.now(timezone.utc)
        db.commit()
    
    finally:
        db.close()