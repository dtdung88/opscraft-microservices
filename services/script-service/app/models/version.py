from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ScriptVersion(Base):
    __tablename__ = "script_versions"

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    change_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))