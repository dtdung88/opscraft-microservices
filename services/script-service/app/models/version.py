from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class ScriptVersion(Base):
    __tablename__ = "script_versions"
    
    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    change_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
    
    script = relationship("Script", back_populates="versions")

@router.post("/{script_id}/versions")
async def create_version(
    script_id: int,
    change_message: str,
    db: Session = Depends(get_db)
):
    """Create new script version"""
    pass

@router.post("/{script_id}/rollback/{version_id}")
async def rollback_to_version(
    script_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """Rollback script to previous version"""
    pass