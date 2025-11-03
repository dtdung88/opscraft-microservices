from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.script import Script, ScriptType, ScriptStatus
from app.schemas.script import ScriptCreate, ScriptUpdate

class ScriptService:
    def __init__(self, db: Session):
        self.db = db
    
    def list_scripts(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        script_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Script]:
        query = self.db.query(Script)
        
        if search:
            query = query.filter(
                (Script.name.ilike(f"%{search}%")) |
                (Script.description.ilike(f"%{search}%"))
            )
        
        if script_type:
            query = query.filter(Script.script_type == script_type)
        
        if status:
            query = query.filter(Script.status == status)
        
        return query.order_by(Script.updated_at.desc()).offset(skip).limit(limit).all()
    
    def get_script(self, script_id: int) -> Optional[Script]:
        return self.db.query(Script).filter(Script.id == script_id).first()
    
    def get_script_by_name(self, name: str) -> Optional[Script]:
        return self.db.query(Script).filter(Script.name == name).first()
    
    def create_script(self, script_data: ScriptCreate, username: str) -> Script:
        script = Script(
            **script_data.dict(),
            created_by=username,
            updated_by=username
        )
        
        self.db.add(script)
        self.db.commit()
        self.db.refresh(script)
        
        return script
    
    def update_script(
        self,
        script_id: int,
        script_data: ScriptUpdate,
        username: str
    ) -> Script:
        script = self.get_script(script_id)
        
        update_dict = script_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(script, key, value)
        
        script.updated_by = username
        
        self.db.commit()
        self.db.refresh(script)
        
        return script
    
    def delete_script(self, script_id: int):
        script = self.get_script(script_id)
        self.db.delete(script)
        self.db.commit()