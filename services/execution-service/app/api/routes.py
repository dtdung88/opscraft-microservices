from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.execution import Execution, ExecutionStatus
from app.schemas.execution import ExecutionCreate, ExecutionResponse
from app.services.execution_service import ExecutionService
from app.workers.celery_worker import execute_script_task
from app.core.events import event_publisher
from config import settings

router = APIRouter()


@router.get("", response_model=List[ExecutionResponse])
async def list_executions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    executions = service.list_executions(skip=skip, limit=limit, status=status)
    return executions


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    execution = service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    execution_data: ExecutionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user = request.state.user
    service = ExecutionService(db)

    execution = service.create_execution(
        execution_data,
        user['username']
    )

    execute_script_task.delay(execution.id)

    await event_publisher.publish(
        "execution-events",
        {
            "event_type": "execution.started",
            "event_id": str(execution.id),
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": execution.id,
            "script_id": execution.script_id,
            "script_name": f"Script {execution.script_id}",
            "executed_by": user['username'],
            "parameters": execution.parameters or {}
        }
    )

    return execution


@router.post("/{execution_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_execution(
    execution_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    execution = service.cancel_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return {"message": "Execution cancelled", "execution_id": execution_id}


@router.get("/stats")
async def get_execution_stats(
    db: Session = Depends(get_db)
):
    """Get execution statistics"""
    from sqlalchemy import func

    total = db.query(func.count(Execution.id)).scalar()
    success = db.query(func.count(Execution.id)).filter(
        Execution.status == ExecutionStatus.SUCCESS
    ).scalar()
    failed = db.query(func.count(Execution.id)).filter(
        Execution.status == ExecutionStatus.FAILED
    ).scalar()
    running = db.query(func.count(Execution.id)).filter(
        Execution.status == ExecutionStatus.RUNNING
    ).scalar()

    return {
        "total_executions": total,
        "success": success,
        "failed": failed,
        "running": running
    }