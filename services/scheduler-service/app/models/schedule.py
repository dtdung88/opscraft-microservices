from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(500))
    script_id = Column(Integer, nullable=False)
    cron_expression = Column(String(100), nullable=False)
    parameters = Column(JSON, default={})
    
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    run_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=False)
    
    timezone = Column(String(50), default='UTC')
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)