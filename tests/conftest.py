"""Pytest configuration and fixtures"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config.service_factory import ServiceFactory
from shared.models.base import Base

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/opscraft_test"
TEST_REDIS_URL = "redis://localhost:6379/15"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create test database session"""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create test Redis client"""
    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_script_data():
    """Test script data"""
    return {
        "name": "Test Script",
        "description": "A test script",
        "script_type": "bash",
        "content": "#!/bin/bash\necho 'Hello World'",
        "parameters": {},
        "tags": ["test"],
    }


@pytest.fixture
def test_secret_data():
    """Test secret data"""
    return {
        "name": "test_secret",
        "value": "super-secret-value",
        "category": "api_key",
        "description": "Test secret",
    }
