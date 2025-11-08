from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ConfigDict

class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    event_category: str
    action: str
    user_id: Optional[int]
    username: str
    user_role: Optional[str]
    ip_address: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    service_name: str
    status: Optional[str]
    risk_level: Optional[str]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AuditSearchRequest(BaseModel):
    user: Optional[str] = None
    resource_type: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    risk_level: Optional[str] = None

class AuditStatistics(BaseModel):
    total_events: int
    events_by_category: Dict[str, int]
    top_users: list
    failed_actions: int
    high_risk_events: int
    success_rate: float