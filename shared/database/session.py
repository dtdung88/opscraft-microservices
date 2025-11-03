"""Database session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.base import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
