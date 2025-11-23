"""Performance and load tests"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient


@pytest.mark.slow
class TestPerformance:
    """Performance tests"""

    def test_concurrent_requests(self, client: TestClient):
        """Test handling concurrent requests"""

        def make_request():
            return client.get("/health")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

    @pytest.mark.asyncio
    async def test_database_query_performance(self, db_session):
        """Test database query performance"""
        import time

        start = time.time()

        # Perform multiple queries
        for _ in range(100):
            db_session.execute("SELECT 1")

        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 1.0  # Less than 1 second for 100 queries
