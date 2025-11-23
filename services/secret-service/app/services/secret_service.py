from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditAction, AuditLog
from app.models.secret import Secret
from app.schemas.secret import SecretCreate, SecretUpdate
from shared.exceptions.custom_exceptions import ValidationError
from shared.security.secrets import secrets_manager
from shared.services.base_service import AuditedService
from shared.validation.validators import InputSanitizer, InputValidator


class SecretService(AuditedService):
    """Secret management service with encryption"""

    def __init__(self, db: Session):
        super().__init__(db, Secret, "secret")

    def _validate_create(self, data: dict) -> None:
        """Validate secret creation"""
        # Validate name
        name = data.get("name", "")
        if not name or len(name) > 255:
            raise ValidationError(
                "Invalid secret name",
                [
                    {
                        "field": "name",
                        "message": "Name is required and must be < 255 chars",
                    }
                ],
            )

        # Check for duplicates
        if self.exists(name=name, is_active=True):
            raise ValidationError(
                "Secret already exists",
                [{"field": "name", "message": f"Secret '{name}' already exists"}],
            )

        # Sanitize inputs
        data["name"] = InputSanitizer.sanitize_html(name)
        if data.get("description"):
            data["description"] = InputSanitizer.sanitize_html(data["description"])

    def create_secret(self, secret_data: SecretCreate, created_by: str) -> Secret:
        """Create secret with encryption"""
        # Encrypt value
        encrypted_value = secrets_manager.encrypt(secret_data.value)

        # Prepare data
        data = secret_data.dict(exclude={"value"})
        data["encrypted_value"] = encrypted_value
        data["created_by"] = created_by
        data["updated_by"] = created_by

        # Create secret
        secret = self.create(data)

        # Log creation
        self._log_audit_event(secret.id, AuditAction.CREATE, created_by)

        return secret

    def get_secret_value(self, secret_id: int, accessed_by: str) -> str:
        """Get decrypted secret value"""
        secret = self.get_or_404(secret_id)

        # Decrypt value
        decrypted = secrets_manager.decrypt(secret.encrypted_value)

        # Update last accessed
        secret.last_accessed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Log access
        self._log_audit_event(secret_id, AuditAction.ACCESS, accessed_by)

        return decrypted

    def update_secret_value(
        self, secret_id: int, new_value: str, updated_by: str
    ) -> Secret:
        """Update secret value"""
        secret = self.get_or_404(secret_id)

        # Encrypt new value
        encrypted_value = secrets_manager.encrypt(new_value)

        # Update
        secret.encrypted_value = encrypted_value
        secret.updated_by = updated_by
        self.db.commit()

        # Log update
        self._log_audit_event(secret_id, AuditAction.UPDATE, updated_by)

        return secret

    def _log_audit_event(self, secret_id: int, action: AuditAction, user: str) -> None:
        """Log audit event"""
        audit = AuditLog(secret_id=secret_id, action=action, user=user)
        self.db.add(audit)
        self.db.commit()

    def get_audit_logs(self, secret_id: int, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for secret"""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.secret_id == secret_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
