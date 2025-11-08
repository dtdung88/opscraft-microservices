from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ConfigDict

class ScheduleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    script_id: int
    cron_expression: str
    parameters: Optional[Dict[str, Any]] = None
    timezone: str = "UTC"
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    @validator('cron_expression')
    def validate_cron(cls, v):
        from croniter import croniter
        if not croniter.is_valid(v):
            raise ValueError('Invalid cron expression')
        return v

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    timezone: Optional[str] = None
    max_retries: Optional[int] = None
    
    @validator('cron_expression')
    def validate_cron(cls, v):
        if v is not None:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError('Invalid cron expression')
        return v

class ScheduleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    script_id: int
    cron_expression: str
    parameters: Optional[Dict[str, Any]]
    is_active: bool
    timezone: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    max_retries: int
    retry_delay_seconds: int
    created_at: datetime
    created_by: str
    
    model_config = ConfigDict(from_attributes=True)