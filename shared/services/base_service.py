"""Base service class with common functionality"""
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from shared.exceptions.custom_exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service with CRUD operations and common patterns"""

    def __init__(self, db: Session, model: Type[ModelType], resource_name: str):
        self.db = db
        self.model = model
        self.resource_name = resource_name

    @contextmanager
    def transaction(self):
        """Database transaction context manager"""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction failed: {e}", exc_info=True)
            raise

    def get(self, id: int) -> Optional[ModelType]:
        """Get single record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.resource_name} {id}: {e}")
            raise

    def get_or_404(self, id: int) -> ModelType:
        """Get record or raise 404"""
        obj = self.get(id)
        if not obj:
            raise ResourceNotFoundError(self.resource_name, id)
        return obj

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        """List records with pagination and filters"""
        try:
            query = self.db.query(self.model)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)

            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))

            return query.offset(skip).limit(limit).all()

        except SQLAlchemyError as e:
            logger.error(f"Failed to list {self.resource_name}s: {e}")
            raise

    def count(self, filters: Optional[dict] = None) -> int:
        """Count records with filters"""
        try:
            query = self.db.query(self.model)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)

            return query.count()

        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.resource_name}s: {e}")
            raise

    def create(self, obj_in: CreateSchemaType, **extra_data) -> ModelType:
        """Create new record"""
        try:
            with self.transaction():
                # Convert Pydantic model to dict
                data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
                data.update(extra_data)

                # Validate before creation
                self._validate_create(data)

                # Create instance
                db_obj = self.model(**data)
                self.db.add(db_obj)
                self.db.flush()
                self.db.refresh(db_obj)

                # Post-creation hook
                self._after_create(db_obj)

                return db_obj

        except SQLAlchemyError as e:
            logger.error(f"Failed to create {self.resource_name}: {e}")
            raise

    def update(self, id: int, obj_in: UpdateSchemaType, **extra_data) -> ModelType:
        """Update existing record"""
        try:
            db_obj = self.get_or_404(id)

            with self.transaction():
                # Get update data
                update_data = (
                    obj_in.dict(exclude_unset=True)
                    if hasattr(obj_in, "dict")
                    else obj_in
                )
                update_data.update(extra_data)

                # Validate before update
                self._validate_update(db_obj, update_data)

                # Update fields
                for field, value in update_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)

                self.db.flush()
                self.db.refresh(db_obj)

                # Post-update hook
                self._after_update(db_obj)

                return db_obj

        except SQLAlchemyError as e:
            logger.error(f"Failed to update {self.resource_name} {id}: {e}")
            raise

    def delete(self, id: int, soft: bool = False) -> bool:
        """Delete record (soft or hard delete)"""
        try:
            db_obj = self.get_or_404(id)

            with self.transaction():
                # Pre-delete hook
                self._before_delete(db_obj)

                if soft and hasattr(self.model, "is_active"):
                    # Soft delete
                    db_obj.is_active = False
                else:
                    # Hard delete
                    self.db.delete(db_obj)

                self.db.flush()

                # Post-delete hook
                self._after_delete(db_obj, soft)

                return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to delete {self.resource_name} {id}: {e}")
            raise

    def exists(self, **filters) -> bool:
        """Check if record exists"""
        query = self.db.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.first() is not None

    def bulk_create(self, objects: List[dict]) -> List[ModelType]:
        """Bulk create records"""
        try:
            with self.transaction():
                db_objects = [self.model(**obj) for obj in objects]
                self.db.bulk_save_objects(db_objects)
                self.db.flush()
                return db_objects

        except SQLAlchemyError as e:
            logger.error(f"Bulk create failed: {e}")
            raise

    # Hooks for subclasses to override
    def _validate_create(self, data: dict) -> None:
        """Validate before creation (override in subclass)"""
        pass

    def _validate_update(self, obj: ModelType, data: dict) -> None:
        """Validate before update (override in subclass)"""
        pass

    def _after_create(self, obj: ModelType) -> None:
        """Hook after creation (override in subclass)"""
        pass

    def _after_update(self, obj: ModelType) -> None:
        """Hook after update (override in subclass)"""
        pass

    def _before_delete(self, obj: ModelType) -> None:
        """Hook before deletion (override in subclass)"""
        pass

    def _after_delete(self, obj: ModelType, soft: bool) -> None:
        """Hook after deletion (override in subclass)"""
        pass


class AuditedService(BaseService):
    """Service with automatic audit logging"""

    def __init__(self, db: Session, model: Type[ModelType], resource_name: str):
        super().__init__(db, model, resource_name)
        self.audit_enabled = True

    def _log_audit(
        self,
        action: str,
        resource_id: int,
        user: str,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ) -> None:
        """Log audit event"""
        if not self.audit_enabled:
            return

        logger.info(
            f"Audit: {action} {self.resource_name} {resource_id}",
            extra={
                "action": action,
                "resource_type": self.resource_name,
                "resource_id": resource_id,
                "user": user,
                "old_value": old_value,
                "new_value": new_value,
            },
        )

    def _after_create(self, obj: ModelType) -> None:
        """Log creation"""
        self._log_audit("create", obj.id, getattr(obj, "created_by", "system"))

    def _after_update(self, obj: ModelType) -> None:
        """Log update"""
        self._log_audit("update", obj.id, getattr(obj, "updated_by", "system"))

    def _after_delete(self, obj: ModelType, soft: bool) -> None:
        """Log deletion"""
        action = "soft_delete" if soft else "delete"
        self._log_audit(action, obj.id, "system")


class CachedService(BaseService):
    """Service with caching support"""

    def __init__(
        self,
        db: Session,
        model: Type[ModelType],
        resource_name: str,
        cache_manager=None,
    ):
        super().__init__(db, model, resource_name)
        self.cache = cache_manager

    async def get_cached(self, id: int) -> Optional[ModelType]:
        """Get from cache or database"""
        if not self.cache:
            return self.get(id)

        cache_key = f"{self.resource_name}:{id}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Get from database and cache
        obj = self.get(id)
        if obj:
            await self.cache.set(cache_key, obj, ttl=300)

        return obj

    async def invalidate_cache(self, id: int) -> None:
        """Invalidate cache for resource"""
        if self.cache:
            cache_key = f"{self.resource_name}:{id}"
            await self.cache.delete(cache_key)

    def _after_update(self, obj: ModelType) -> None:
        """Invalidate cache on update"""
        import asyncio

        asyncio.create_task(self.invalidate_cache(obj.id))

    def _after_delete(self, obj: ModelType, soft: bool) -> None:
        """Invalidate cache on delete"""
        import asyncio

        asyncio.create_task(self.invalidate_cache(obj.id))
