"""Integration tests for auth service"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthService:
    """Test authentication service"""

    def test_register_user(self, client: TestClient, test_user_data):
        """Test user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client: TestClient, test_user_data):
        """Test registering with duplicate username"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register again
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 409

    def test_login_success(self, client: TestClient, test_user_data):
        """Test successful login"""
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient, test_user_data):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"},
        )

        assert response.status_code == 401
