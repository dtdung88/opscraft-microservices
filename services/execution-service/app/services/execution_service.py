from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.execution import Execution, ExecutionStatus
from app.schemas.execution import ExecutionCreate
from shared.exceptions.custom_exceptions import (
    ExecutionError,
    ResourceNotFoundError,
    ValidationError,
)
from shared.services.base_service import AuditedService, CachedService


class ExecutionService(AuditedService, CachedService):
    """Execution management service"""

    def __init__(self, db: Session, cache_manager=None):
        super().__init__(db, Execution, "execution")
        self.cache = cache_manager

    def _validate_create(self, data: dict) -> None:
        """Validate execution creation"""
        script_id = data.get("script_id")
        if not script_id:
            raise ValidationError(
                "Script ID required",
                [{"field": "script_id", "message": "Script ID is required"}],
            )

        # Validate parameters if provided
        parameters = data.get("parameters", {})
        if parameters and not isinstance(parameters, dict):
            raise ValidationError(
                "Invalid parameters",
                [{"field": "parameters", "message": "Parameters must be a dictionary"}],
            )

    def create_execution(
        self, execution_data: ExecutionCreate, executed_by: str
    ) -> Execution:
        """Create new execution"""
        data = execution_data.dict()
        data["executed_by"] = executed_by
        data["status"] = ExecutionStatus.PENDING

        return self.create(data)

    def update_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Execution:
        """Update execution status"""
        execution = self.get_or_404(execution_id)

        with self.transaction():
            execution.status = status

            if output:
                execution.output = output

            if error:
                execution.error = error

            if status in [
                ExecutionStatus.SUCCESS,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            ]:
                execution.completed_at = datetime.now(timezone.utc)

            self.db.flush()
            self.db.refresh(execution)

            return execution

    def cancel_execution(self, execution_id: int, cancelled_by: str) -> Execution:
        """Cancel running execution"""
        execution = self.get_or_404(execution_id)

        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            raise ExecutionError(
                f"Cannot cancel execution in {execution.status} state", execution_id
            )

        return self.update_status(
            execution_id,
            ExecutionStatus.CANCELLED,
            error=f"Cancelled by {cancelled_by}",
        )

    def get_active_executions(self) -> List[Execution]:
        """Get all active executions"""
        return self.list(filters={"status": ExecutionStatus.RUNNING}, limit=1000)

    def get_user_executions(
        self, username: str, skip: int = 0, limit: int = 100
    ) -> List[Execution]:
        """Get executions for a user"""
        return self.list(
            filters={"executed_by": username},
            order_by="started_at",
            skip=skip,
            limit=limit,
        )
