from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models.execution import Execution, ExecutionStatus
from app.schemas.execution import ExecutionCreate

class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
    
    def list_executions(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Execution]:
        query = self.db.query(Execution)
        
        if status:
            query = query.filter(Execution.status == status)
        
        return query.order_by(
            Execution.started_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_execution(self, execution_id: int) -> Optional[Execution]:
        return self.db.query(Execution).filter(
            Execution.id == execution_id
        ).first()
    
    def create_execution(
        self,
        execution_data: ExecutionCreate,
        username: str
    ) -> Execution:
        execution = Execution(
            script_id=execution_data.script_id,
            parameters=execution_data.parameters,
            status=ExecutionStatus.PENDING,
            executed_by=username
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        return execution
    
    def update_execution_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        execution = self.get_execution(execution_id)
        
        if execution:
            execution.status = status
            
            if output:
                execution.output = output
            
            if error:
                execution.error = error
            
            if status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                execution.completed_at = datetime.now(timezone.utc)
            
            self.db.commit()
    
    def cancel_execution(self, execution_id: int) -> Optional[Execution]:
        execution = self.get_execution(execution_id)
        
        if execution and execution.status == ExecutionStatus.PENDING:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return execution
        
        return None