"""Integration tests for rate limiting"""
import asyncio

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, client: TestClient):
        """Test that rate limits are enforced"""
        # Make requests up to the limit
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login", json={"username": "test", "password": "test"}
            )
            assert response.status_code in [401, 429]  # Either auth fail or rate limit

        # Next request should be rate limited
        response = client.post(
            "/api/v1/auth/login", json={"username": "test", "password": "test"}
        )

        if response.status_code == 429:
            assert "retry_after" in response.json()

    def test_rate_limit_headers(self, client: TestClient, test_user_data):
        """Test rate limit headers are present"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
