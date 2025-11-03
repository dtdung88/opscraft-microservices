from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ScriptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    script_type: str
    content: str
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: str = "1.0.0"

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None

class ScriptResponse(ScriptBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True