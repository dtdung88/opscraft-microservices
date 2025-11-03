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
from shared.events.event_schemas import ExecutionStartedEvent

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
    
    # Create execution record
    execution = service.create_execution(
        execution_data,
        user['username']
    )
    
    # Queue execution task
    execute_script_task.delay(execution.id)
    
    # Publish event
    await event_publisher.publish(
        "execution-events",
        ExecutionStartedEvent(
            event_id=str(execution.id),
            service="execution-service",
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_id=execution.id,
            script_id=execution.script_id,
            script_name=f"Script {execution.script_id}",
            executed_by=user['username'],
            parameters=execution.parameters or {}
        ).dict()
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