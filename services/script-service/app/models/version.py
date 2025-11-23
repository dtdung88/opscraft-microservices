"""Script version model for version control."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ScriptVersion(Base):
    """Stores historical versions of scripts for version control."""

    __tablename__ = "script_versions"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(
        Integer,
        ForeignKey("scripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    change_message = Column(Text)
    checksum = Column(String(64))  # SHA-256 hash of content
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=False)

    # Unique constraint on script_id + version
    __table_args__ = (
        {"schema": None},
    )

    def __repr__(self) -> str:
        return f"<ScriptVersion(script_id={self.script_id}, version={self.version})>"
