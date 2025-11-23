"""Refactored script service with best practices"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.script import Script, ScriptStatus, ScriptType
from app.schemas.script import ScriptCreate, ScriptUpdate
from shared.exceptions.custom_exceptions import (
    ResourceAlreadyExistsError,
    ScriptValidationError,
    ValidationError,
)
from shared.services.base_service import AuditedService, CachedService
from shared.validation.validators import (
    InputSanitizer,
    InputValidator,
    ValidationResult,
)


class ScriptService(AuditedService, CachedService):
    """Production-ready script service with full validation and caching"""

    def __init__(self, db: Session, cache_manager=None):
        super().__init__(db, Script, "script")
        self.cache = cache_manager

    def _validate_create(self, data: dict) -> None:
        """Validate script before creation"""
        # Validate script name
        name_result = InputValidator.validate_script_name(data.get("name", ""))
        if not name_result:
            raise ValidationError(
                "Invalid script name",
                [{"field": "name", "message": name_result.message}],
            )

        # Check for duplicates
        if self.exists(name=data["name"]):
            raise ResourceAlreadyExistsError("script", data["name"])

        # Validate content
        content = data.get("content", "")
        script_type = data.get("script_type", "bash")

        content_result = self._validate_script_content(content, script_type)
        if not content_result:
            raise ScriptValidationError(
                "Script content validation failed", content_result.errors
            )

        # Sanitize inputs
        data["name"] = InputSanitizer.sanitize_html(data["name"])
        if data.get("description"):
            data["description"] = InputSanitizer.sanitize_html(data["description"])

    def _validate_update(self, obj: Script, data: dict) -> None:
        """Validate script before update"""
        # Validate name if changed
        if "name" in data and data["name"] != obj.name:
            name_result = InputValidator.validate_script_name(data["name"])
            if not name_result:
                raise ValidationError(
                    "Invalid script name",
                    [{"field": "name", "message": name_result.message}],
                )

            # Check for duplicates
            if self.exists(name=data["name"]):
                raise ResourceAlreadyExistsError("script", data["name"])

        # Validate content if changed
        if "content" in data:
            script_type = data.get("script_type", obj.script_type)
            content_result = self._validate_script_content(data["content"], script_type)
            if not content_result:
                raise ScriptValidationError(
                    "Script content validation failed", content_result.errors
                )

    def _validate_script_content(
        self, content: str, script_type: str
    ) -> ValidationResult:
        """Comprehensive script content validation"""
        errors = []

        # Check length
        if not content or len(content.strip()) == 0:
            errors.append("Script content cannot be empty")

        if len(content) > 1_000_000:  # 1MB limit
            errors.append("Script content too large (max 1MB)")

        # Security checks
        security_result = InputValidator.detect_security_threats(content)
        if not security_result:
            errors.extend(security_result.errors)

        # Type-specific validation
        if script_type == "bash":
            if not content.strip().startswith("#!"):
                errors.append("Bash script should start with shebang (#!/bin/bash)")

            # Check for basic syntax (simple check)
            dangerous_patterns = ["rm -rf /", "dd if=/dev/", ":(){ :|:& };:"]
            for pattern in dangerous_patterns:
                if pattern in content:
                    errors.append(f"Dangerous pattern detected: {pattern}")

        elif script_type == "python":
            # Try to compile Python code
            try:
                compile(content, "<string>", "exec")
            except SyntaxError as e:
                errors.append(f"Python syntax error: {e.msg} at line {e.lineno}")

        if errors:
            return ValidationResult(False, "Validation failed", errors)

        return ValidationResult(True, "Valid script content")

    def list_by_user(
        self, username: str, skip: int = 0, limit: int = 100
    ) -> List[Script]:
        """List scripts created by user"""
        return self.list(
            skip=skip,
            limit=limit,
            filters={"created_by": username},
            order_by="updated_at",
        )

    def search(
        self,
        query: str,
        script_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Script]:
        """Search scripts with filters"""
        db_query = self.db.query(self.model)

        # Text search
        if query:
            search_filter = self.model.name.ilike(
                f"%{query}%"
            ) | self.model.description.ilike(f"%{query}%")
            db_query = db_query.filter(search_filter)

        # Type filter
        if script_type:
            db_query = db_query.filter(self.model.script_type == script_type)

        # Status filter
        if status:
            db_query = db_query.filter(self.model.status == status)

        return (
            db_query.order_by(self.model.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self, script_id: int, status: ScriptStatus, updated_by: str
    ) -> Script:
        """Update script status"""
        script = self.get_or_404(script_id)

        with self.transaction():
            script.status = status
            script.updated_by = updated_by
            self.db.flush()
            self.db.refresh(script)

            self._after_update(script)

            return script

    def clone(self, script_id: int, new_name: str, created_by: str) -> Script:
        """Clone an existing script"""
        original = self.get_or_404(script_id)

        # Create new script with copied content
        clone_data = ScriptCreate(
            name=new_name,
            description=f"Cloned from {original.name}",
            script_type=original.script_type,
            content=original.content,
            parameters=original.parameters,
            tags=original.tags or [],
        )

        return self.create(clone_data, created_by=created_by, updated_by=created_by)

    def get_statistics(self) -> dict:
        """Get script statistics"""
        from sqlalchemy import func

        stats = {
            "total": self.count(),
            "active": self.count({"status": ScriptStatus.ACTIVE}),
            "by_type": {},
        }

        # Count by type
        type_counts = (
            self.db.query(self.model.script_type, func.count(self.model.id))
            .group_by(self.model.script_type)
            .all()
        )

        stats["by_type"] = {
            str(script_type): count for script_type, count in type_counts
        }

        return stats
