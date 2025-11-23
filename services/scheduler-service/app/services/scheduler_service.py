from datetime import datetime, timezone
from typing import Optional

from croniter import croniter
from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from shared.exceptions.custom_exceptions import ValidationError
from shared.services.base_service import AuditedService
from shared.validation.validators import InputValidator


class SchedulerService(AuditedService):
    """Schedule management service"""

    def __init__(self, db: Session):
        super().__init__(db, Schedule, "schedule")

    def _validate_create(self, data: dict) -> None:
        """Validate schedule creation"""
        # Validate name
        name = data.get("name", "")
        if not name or len(name) > 255:
            raise ValidationError(
                "Invalid schedule name",
                [
                    {
                        "field": "name",
                        "message": "Name is required and must be < 255 chars",
                    }
                ],
            )

        # Check for duplicates
        if self.exists(name=name, is_active=True):
            raise ValidationError(
                "Schedule already exists",
                [{"field": "name", "message": f"Schedule '{name}' already exists"}],
            )

        # Validate cron expression
        cron_result = InputValidator.validate_cron_expression(
            data.get("cron_expression", "")
        )
        if not cron_result:
            raise ValidationError(
                "Invalid cron expression",
                [{"field": "cron_expression", "message": cron_result.message}],
            )

    def create_schedule(
        self, schedule_data: ScheduleCreate, created_by: str
    ) -> Schedule:
        """Create new schedule"""
        # Calculate next run time
        cron = croniter(schedule_data.cron_expression, datetime.now(timezone.utc))
        next_run = cron.get_next(datetime)

        # Prepare data
        data = schedule_data.dict()
        data["created_by"] = created_by
        data["next_run"] = next_run

        return self.create(data)

    def update_schedule_status(self, schedule_id: int, is_active: bool) -> Schedule:
        """Enable/disable schedule"""
        schedule = self.get_or_404(schedule_id)
        schedule.is_active = is_active
        self.db.commit()
        return schedule

    def record_execution(self, schedule_id: int, success: bool) -> Schedule:
        """Record schedule execution"""
        schedule = self.get_or_404(schedule_id)

        with self.transaction():
            schedule.last_run = datetime.now(timezone.utc)
            schedule.run_count += 1

            # Calculate next run
            cron = croniter(schedule.cron_expression, schedule.last_run)
            schedule.next_run = cron.get_next(datetime)

            self.db.flush()
            self.db.refresh(schedule)

            return schedule
