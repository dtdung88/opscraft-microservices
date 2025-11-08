from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from apscheduler.triggers.cron import CronTrigger
import httpx

from app.db.session import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.services.scheduler_service import SchedulerService
from config import settings

router = APIRouter()

async def execute_scheduled_script(schedule_id: int):
    """Execute a scheduled script"""
    db = next(get_db())
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not schedule or not schedule.is_active:
        return
    
    # Trigger execution via Execution Service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.EXECUTION_SERVICE_URL}/api/v1/executions",
                json={
                    "script_id": schedule.script_id,
                    "parameters": schedule.parameters
                },
                headers={"X-Scheduled": "true"},
                timeout=30.0
            )
            
            if response.status_code == 201:
                schedule.last_run = datetime.now(timezone.utc)
                schedule.run_count += 1
                db.commit()
        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule_id}: {e}")
    
    db.close()

@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    service = SchedulerService(db)
    return service.list_schedules(skip, limit, active_only)

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    service = SchedulerService(db)
    schedule = service.get_schedule(schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return schedule

@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user = request.state.user
    service = SchedulerService(db)
    
    # Create schedule in database
    schedule = service.create_schedule(schedule_data, user['username'])
    
    # Add job to scheduler
    scheduler = request.app.state.scheduler
    trigger = CronTrigger.from_crontab(schedule.cron_expression)
    
    scheduler.add_job(
        execute_scheduled_script,
        trigger=trigger,
        id=f"schedule_{schedule.id}",
        args=[schedule.id],
        replace_existing=True
    )
    
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    service = SchedulerService(db)
    schedule = service.update_schedule(schedule_id, schedule_data)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Update scheduler job
    scheduler = request.app.state.scheduler
    job_id = f"schedule_{schedule.id}"
    
    if schedule.is_active:
        trigger = CronTrigger.from_crontab(schedule.cron_expression)
        scheduler.add_job(
            execute_scheduled_script,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True
        )
    else:
        scheduler.remove_job(job_id)
    
    return schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    service = SchedulerService(db)
    service.delete_schedule(schedule_id)
    
    # Remove from scheduler
    scheduler = request.app.state.scheduler
    try:
        scheduler.remove_job(f"schedule_{schedule_id}")
    except:
        pass
    
    return None

@router.post("/{schedule_id}/trigger")
async def trigger_schedule_now(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    \"\"\"Manually trigger a schedule execution\"\"\"
    await execute_scheduled_script(schedule_id)
    return {"message": "Schedule triggered successfully"}