from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ConfigDict

class ExecutionCreate(BaseModel):
    script_id: int
    parameters: Optional[Dict[str, Any]] = None

class ExecutionResponse(BaseModel):
    id: int
    script_id: int
    status: str
    parameters: Optional[Dict[str, Any]]
    output: Optional[str]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    executed_by: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)