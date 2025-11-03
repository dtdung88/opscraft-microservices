from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class Secret(Base):
    __tablename__ = "secrets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    encrypted_value = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # api_key, password, token, certificate
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)