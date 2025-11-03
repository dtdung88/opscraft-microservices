import pytest
import httpx
from typing import Dict

BASE_URL = "http://localhost:8000"

@pytest.fixture
async def test_user() -> Dict:
    """Create a test user"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }

@pytest.mark.asyncio
async def test_user_registration(test_user):
    """Test user registration flow"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert "id" in data

@pytest.mark.asyncio
async def test_user_login(test_user):
    """Test user login flow"""
    async with httpx.AsyncClient() as client:
        # First register
        await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_user
        )
        
        # Then login
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_current_user(test_user):
    """Test getting current user info"""
    async with httpx.AsyncClient() as client:
        # Register and login
        await client.post(f"{BASE_URL}/api/v1/auth/register", json=test_user)
        
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user
        response = await client.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user["username"]

@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test unauthorized access is denied"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/auth/me")
        assert response.status_code == 401