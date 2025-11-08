from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class SecretCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value: str
    category: Optional[str] = None

class SecretUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    category: Optional[str] = None

class SecretResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    value: Optional[str] = None  # Only included if reveal=True
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    is_active: bool
    last_accessed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    secret_id: int
    action: str
    user: str
    ip_address: Optional[str]
    timestamp: datetime
    details: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)