import pytest
import httpx
import asyncio
from typing import Dict

BASE_URL = "http://localhost:8000"

@pytest.fixture
async def auth_token() -> str:
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        # Register user
        await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": "scripttester",
                "email": "script@example.com",
                "password": "TestPass123!",
                "full_name": "Script Tester"
            }
        )
        
        # Login
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "scripttester",
                "password": "TestPass123!"
            }
        )
        
        return response.json()["access_token"]

@pytest.mark.asyncio
async def test_create_script(auth_token):
    """Test script creation"""
    async with httpx.AsyncClient() as client:
        script_data = {
            "name": "Test Script",
            "description": "A test bash script",
            "script_type": "bash",
            "content": "echo 'Hello World'",
            "parameters": {},
            "tags": ["test"]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/scripts",
            json=script_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == script_data["name"]
        assert data["script_type"] == "bash"
        assert "id" in data

@pytest.mark.asyncio
async def test_list_scripts(auth_token):
    """Test listing scripts"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/scripts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_execute_script(auth_token):
    """Test script execution"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create script
        script_response = await client.post(
            f"{BASE_URL}/api/v1/scripts",
            json={
                "name": "Exec Test Script",
                "script_type": "bash",
                "content": "echo 'Test execution'"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        script_id = script_response.json()["id"]
        
        # Execute script
        exec_response = await client.post(
            f"{BASE_URL}/api/v1/executions",
            json={
                "script_id": script_id,
                "parameters": {}
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert exec_response.status_code == 201
        exec_data = exec_response.json()
        assert exec_data["script_id"] == script_id
        assert exec_data["status"] in ["pending", "running"]
        
        # Wait for execution to complete
        execution_id = exec_data["id"]
        for _ in range(30):
            status_response = await client.get(
                f"{BASE_URL}/api/v1/executions/{execution_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            status_data = status_response.json()
            if status_data["status"] in ["success", "failed"]:
                break
            
            await asyncio.sleep(1)
        
        assert status_data["status"] == "success"

@pytest.mark.asyncio
async def test_get_execution_logs(auth_token):
    """Test retrieving execution logs"""
    async with httpx.AsyncClient() as client:
        # List executions
        response = await client.get(
            f"{BASE_URL}/api/v1/executions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)