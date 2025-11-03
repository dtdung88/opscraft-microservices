"""HTTP client for inter-service communication"""
import httpx
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class ServiceClient:
    """HTTP client for calling other microservices"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get(self, path: str, headers: Optional[Dict] = None):
        """GET request"""
        try:
            url = f"{self.base_url}{path}"
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Service call failed: {e}")
            raise
    
    async def post(self, path: str, json: dict, headers: Optional[Dict] = None):
        """POST request"""
        try:
            url = f"{self.base_url}{path}"
            response = await self.client.post(url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Service call failed: {e}")
            raise
    
    async def close(self):
        """Close client"""
        await self.client.aclose()
