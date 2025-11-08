from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from croniter import croniter

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate

class SchedulerService:
    def __init__(self, db: Session):
        self.db = db
    
    def list_schedules(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Schedule]:
        query = self.db.query(Schedule)
        
        if active_only:
            query = query.filter(Schedule.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def get_schedule(self, schedule_id: int) -> Optional[Schedule]:
        return self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    def create_schedule(
        self,
        schedule_data: ScheduleCreate,
        username: str
    ) -> Schedule:
        # Calculate next run time
        cron = croniter(schedule_data.cron_expression, datetime.now(timezone.utc))
        next_run = cron.get_next(datetime)
        
        schedule = Schedule(
            name=schedule_data.name,
            description=schedule_data.description,
            script_id=schedule_data.script_id,
            cron_expression=schedule_data.cron_expression,
            parameters=schedule_data.parameters,
            timezone=schedule_data.timezone,
            max_retries=schedule_data.max_retries,
            retry_delay_seconds=schedule_data.retry_delay_seconds,
            next_run=next_run,
            created_by=username
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def update_schedule(
        self,
        schedule_id: int,
        schedule_data: ScheduleUpdate
    ) -> Optional[Schedule]:
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return None
        
        update_dict = schedule_data.dict(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(schedule, key, value)
        
        # Recalculate next run if cron changed
        if 'cron_expression' in update_dict:
            cron = croniter(schedule.cron_expression, datetime.now(timezone.utc))
            schedule.next_run = cron.get_next(datetime)
        
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def delete_schedule(self, schedule_id: int):
        schedule = self.get_schedule(schedule_id)
        if schedule:
            self.db.delete(schedule)
            self.db.commit()