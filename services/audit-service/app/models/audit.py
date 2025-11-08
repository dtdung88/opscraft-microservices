from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event information
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # auth, script, execution, secret, admin
    action = Column(String(100), nullable=False)
    
    # Actor information
    user_id = Column(Integer, index=True)
    username = Column(String(255), nullable=False, index=True)
    user_role = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Resource information
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100))
    resource_name = Column(String(255))
    
    # Request details
    service_name = Column(String(50), nullable=False)
    endpoint = Column(String(255))
    http_method = Column(String(10))
    request_id = Column(String(100), index=True)
    correlation_id = Column(String(100), index=True)
    
    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    metadata = Column(JSON)
    
    # Result
    status = Column(String(20))  # success, failure, error
    error_message = Column(Text)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Security
    risk_level = Column(String(20))  # low, medium, high, critical
    flagged = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_user_timestamp', 'username', 'timestamp'),
        Index('idx_resource_timestamp', 'resource_type', 'resource_id', 'timestamp'),
        Index('idx_event_timestamp', 'event_type', 'timestamp'),
    )

class AuditReport(Base):
    __tablename__ = "audit_reports"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    report_type = Column(String(50))  # user_activity, security, compliance, system
    filters = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
    
    schedule = Column(String(100))  # cron expression for scheduled reports
    recipients = Column(JSON)  # email addresses
    
    is_active = Column(Boolean, default=True)