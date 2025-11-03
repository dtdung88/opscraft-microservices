from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

class ScriptType(str, enum.Enum):
    BASH = "bash"
    PYTHON = "python"
    ANSIBLE = "ansible"
    TERRAFORM = "terraform"

class ScriptStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    script_type = Column(SQLEnum(ScriptType), nullable=False)
    content = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(SQLEnum(ScriptStatus), default=ScriptStatus.ACTIVE)
    version = Column(String(50), nullable=False, default="1.0.0")
    tags = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=False)