from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic
from app.models.secret import Secret
from app.models.audit import AuditLog