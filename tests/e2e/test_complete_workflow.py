import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_complete_workflow():
    """
    Test complete workflow:
    1. Register user
    2. Login
    3. Create secret
    4. Create script that uses secret
    5. Execute script
    6. Monitor execution
    7. Verify results
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Register user
        user_data = {
            "username": "e2e_tester",
            "email": "e2e@example.com",
            "password": "E2ETest123!",
            "full_name": "E2E Tester"
        }
        
        register_response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data
        )
        assert register_response.status_code == 201
        
        # Step 2: Login
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Create secret
        secret_response = await client.post(
            f"{BASE_URL}/api/v1/secrets",
            json={
                "name": "e2e_api_key",
                "value": "my-secret-api-key-12345",
                "category": "api_key",
                "description": "E2E test API key"
            },
            headers=headers
        )
        assert secret_response.status_code == 201
        secret_id = secret_response.json()["id"]
        
        # Step 4: Create script
        script_response = await client.post(
            f"{BASE_URL}/api/v1/scripts",
            json={
                "name": "E2E Test Script",
                "description": "End-to-end test script",
                "script_type": "bash",
                "content": """
                    #!/bin/bash
                    echo "Starting E2E test script"
                    echo "API Key: $API_KEY"
                    echo "Script completed successfully"
                """,
                "parameters": {
                    "API_KEY": {"type": "secret", "secret_id": secret_id}
                },
                "tags": ["e2e", "test"]
            },
            headers=headers
        )
        assert script_response.status_code == 201
        script_id = script_response.json()["id"]
        
        # Step 5: Execute script
        execution_response = await client.post(
            f"{BASE_URL}/api/v1/executions",
            json={
                "script_id": script_id,
                "parameters": {}
            },
            headers=headers
        )
        assert execution_response.status_code == 201
        execution_id = execution_response.json()["id"]
        
        # Step 6: Monitor execution
        max_retries = 30
        execution_status = None
        
        for _ in range(max_retries):
            status_response = await client.get(
                f"{BASE_URL}/api/v1/executions/{execution_id}",
                headers=headers
            )
            
            execution_data = status_response.json()
            execution_status = execution_data["status"]
            
            if execution_status in ["success", "failed"]:
                break
            
            await asyncio.sleep(2)
        
        # Step 7: Verify results
        assert execution_status == "success", f"Execution failed with status: {execution_status}"
        
        # Verify audit logs for secret access
        audit_response = await client.get(
            f"{BASE_URL}/api/v1/secrets/{secret_id}/audit",
            headers=headers
        )
        assert audit_response.status_code == 200
        audit_logs = audit_response.json()
        
        # Should have at least one access log
        assert len(audit_logs) > 0
        
        # Verify system stats (admin endpoint)
        stats_response = await client.get(
            f"{BASE_URL}/api/v1/admin/stats",
            headers=headers
        )
        
        # This might fail if user is not admin, which is expected
        if stats_response.status_code == 200:
            stats = stats_response.json()
            assert "summary" in stats
            assert stats["summary"]["total_executions"] >= 1

@pytest.mark.asyncio
async def test_concurrent_executions():
    """Test multiple concurrent script executions"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Setup: Register and login
        await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": "concurrent_tester",
                "email": "concurrent@example.com",
                "password": "Concurrent123!",
                "full_name": "Concurrent Tester"
            }
        )
        
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "concurrent_tester",
                "password": "Concurrent123!"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create script
        script_response = await client.post(
            f"{BASE_URL}/api/v1/scripts",
            json={
                "name": "Concurrent Test Script",
                "script_type": "bash",
                "content": "sleep 2 && echo 'Done'"
            },
            headers=headers
        )
        script_id = script_response.json()["id"]
        
        # Launch 5 concurrent executions
        execution_ids = []
        for i in range(5):
            exec_response = await client.post(
                f"{BASE_URL}/api/v1/executions",
                json={"script_id": script_id, "parameters": {}},
                headers=headers
            )
            execution_ids.append(exec_response.json()["id"])
        
        # Wait for all to complete
        await asyncio.sleep(10)
        
        # Verify all completed
        success_count = 0
        for exec_id in execution_ids:
            status_response = await client.get(
                f"{BASE_URL}/api/v1/executions/{exec_id}",
                headers=headers
            )
            if status_response.json()["status"] == "success":
                success_count += 1
        
        assert success_count >= 4, "Most concurrent executions should succeed"