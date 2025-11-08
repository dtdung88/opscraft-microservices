from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ConfigDict

class ApprovalCreate(BaseModel):
    approval_type: str
    resource_type: str
    resource_id: int
    action: str
    reason: Optional[str] = None
    metadata: Optional[str] = None

class ApprovalDecision(BaseModel):
    approved: bool
    comment: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: int
    approval_type: str
    status: str
    requester: str
    resource_type: str
    resource_id: int
    action: str
    reason: Optional[str]
    metadata: Optional[str]
    approver: Optional[str]
    approval_comment: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    approved_at: Optional[datetime]
    requires_approval_count: int
    approval_count: int
    
    model_config = ConfigDict(from_attributes=True)

class ApprovalRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    approval_type: str
    conditions: Optional[str] = None
    required_approvers_count: int = 1
    required_approver_roles: Optional[str] = None