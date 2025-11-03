from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models.secret import Secret
from app.models.audit import AuditLog, AuditAction
from app.schemas.secret import SecretCreate, SecretUpdate, SecretResponse
from app.core.encryption import EncryptionService

class SecretService:
    def __init__(self, db: Session, encryption_service: EncryptionService):
        self.db = db
        self.encryption = encryption_service
    
    def list_secrets(self, skip: int = 0, limit: int = 100) -> List[Secret]:
        return self.db.query(Secret).filter(
            Secret.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_secret(self, secret_id: int, reveal: bool = False, user: str = None) -> Optional[SecretResponse]:
        secret = self.db.query(Secret).filter(
            Secret.id == secret_id,
            Secret.is_active == True
        ).first()
        
        if not secret:
            return None
        
        response = SecretResponse.from_orm(secret)
        
        if reveal:
            # Decrypt value
            response.value = self.encryption.decrypt(secret.encrypted_value)
            
            # Log access
            self._log_audit(secret_id, AuditAction.ACCESS, user or "unknown")
            
            # Update last accessed
            secret.last_accessed_at = datetime.now(timezone.utc)
            self.db.commit()
        
        return response
    
    def create_secret(self, secret_data: SecretCreate, user: str) -> Secret:
        # Encrypt value
        encrypted_value = self.encryption.encrypt(secret_data.value)
        
        secret = Secret(
            name=secret_data.name,
            description=secret_data.description,
            encrypted_value=encrypted_value,
            category=secret_data.category,
            created_by=user,
            updated_by=user
        )
        
        self.db.add(secret)
        self.db.commit()
        self.db.refresh(secret)
        
        # Log creation
        self._log_audit(secret.id, AuditAction.CREATE, user)
        
        return secret
    
    def update_secret(self, secret_id: int, secret_data: SecretUpdate, user: str) -> Optional[Secret]:
        secret = self.db.query(Secret).filter(Secret.id == secret_id).first()
        
        if not secret:
            return None
        
        update_dict = secret_data.dict(exclude_unset=True)
        
        if 'value' in update_dict:
            update_dict['encrypted_value'] = self.encryption.encrypt(update_dict.pop('value'))
        
        for key, value in update_dict.items():
            setattr(secret, key, value)
        
        secret.updated_by = user
        self.db.commit()
        self.db.refresh(secret)
        
        # Log update
        self._log_audit(secret_id, AuditAction.UPDATE, user)
        
        return secret
    
    def delete_secret(self, secret_id: int, user: str):
        secret = self.db.query(Secret).filter(Secret.id == secret_id).first()
        
        if secret:
            secret.is_active = False
            secret.updated_by = user
            self.db.commit()
            
            # Log deletion
            self._log_audit(secret_id, AuditAction.DELETE, user)
    
    def get_audit_logs(self, secret_id: int) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.secret_id == secret_id
        ).order_by(AuditLog.timestamp.desc()).all()
    
    def _log_audit(self, secret_id: int, action: AuditAction, user: str):
        log = AuditLog(
            secret_id=secret_id,
            action=action,
            user=user
        )
        self.db.add(log)
        self.db.commit()