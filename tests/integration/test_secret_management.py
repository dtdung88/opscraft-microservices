import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.fixture
async def auth_token() -> str:
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": "secrettester",
                "email": "secret@example.com",
                "password": "SecretPass123!",
                "full_name": "Secret Tester"
            }
        )
        
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "secrettester",
                "password": "SecretPass123!"
            }
        )
        
        return response.json()["access_token"]

@pytest.mark.asyncio
async def test_create_secret(auth_token):
    """Test secret creation"""
    async with httpx.AsyncClient() as client:
        secret_data = {
            "name": "test_api_key",
            "description": "Test API key",
            "value": "super-secret-api-key-12345",
            "category": "api_key"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json=secret_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == secret_data["name"]
        assert "value" not in data  # Value should be encrypted
        assert "id" in data

@pytest.mark.asyncio
async def test_list_secrets(auth_token):
    """Test listing secrets"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/secrets",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_reveal_secret(auth_token):
    """Test revealing encrypted secret"""
    async with httpx.AsyncClient() as client:
        # Create secret
        create_response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json={
                "name": "reveal_test",
                "value": "secret-value-123",
                "category": "password"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        secret_id = create_response.json()["id"]
        
        # Get secret without revealing
        response = await client.get(
            f"{BASE_URL}/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "value" not in data or data["value"] is None
        
        # Get secret with reveal=true
        reveal_response = await client.get(
            f"{BASE_URL}/api/v1/secrets/{secret_id}?reveal=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert reveal_response.status_code == 200
        reveal_data = reveal_response.json()
        assert reveal_data["value"] == "secret-value-123"

@pytest.mark.asyncio
async def test_update_secret(auth_token):
    """Test updating secret"""
    async with httpx.AsyncClient() as client:
        # Create secret
        create_response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json={
                "name": "update_test",
                "value": "old-value"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        secret_id = create_response.json()["id"]
        
        # Update secret
        update_response = await client.put(
            f"{BASE_URL}/api/v1/secrets/{secret_id}",
            json={
                "value": "new-value",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert update_response.status_code == 200

@pytest.mark.asyncio
async def test_delete_secret(auth_token):
    """Test deleting secret"""
    async with httpx.AsyncClient() as client:
        # Create secret
        create_response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json={
                "name": "delete_test",
                "value": "will-be-deleted"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        secret_id = create_response.json()["id"]
        
        # Delete secret
        delete_response = await client.delete(
            f"{BASE_URL}/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert delete_response.status_code == 204

@pytest.mark.asyncio
async def test_secret_audit_logs(auth_token):
    """Test secret audit logging"""
    async with httpx.AsyncClient() as client:
        # Create secret
        create_response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json={
                "name": "audit_test",
                "value": "audit-value"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        secret_id = create_response.json()["id"]
        
        # Access secret to generate audit log
        await client.get(
            f"{BASE_URL}/api/v1/secrets/{secret_id}?reveal=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Get audit logs
        audit_response = await client.get(
            f"{BASE_URL}/api/v1/secrets/{secret_id}/audit",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert audit_response.status_code == 200
        logs = audit_response.json()
        assert isinstance(logs, list)
        assert len(logs) > 0