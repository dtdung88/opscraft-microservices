from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ApprovalType(str, enum.Enum):
    SCRIPT_EXECUTION = "script_execution"
    SCRIPT_MODIFICATION = "script_modification"
    SECRET_ACCESS = "secret_access"
    USER_ROLE_CHANGE = "user_role_change"

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    approval_type = Column(SQLEnum(ApprovalType), nullable=False)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    
    # Request details
    requester = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    reason = Column(Text)
    metadata = Column(Text)
    
    # Approval details
    approver = Column(String(255))
    approval_comment = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Configuration
    requires_approval_count = Column(Integer, default=1)
    approval_count = Column(Integer, default=0)
    auto_approve = Column(Boolean, default=False)

class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    approval_type = Column(SQLEnum(ApprovalType), nullable=False)
    conditions = Column(Text)  # JSON conditions
    
    required_approvers_count = Column(Integer, default=1)
    required_approver_roles = Column(Text)  # JSON array of roles
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=False)