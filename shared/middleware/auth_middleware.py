from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthMiddleware:
    def __init__(self, auth_service_url: str):
        self.auth_service_url = auth_service_url
    
    async def verify_token(self, token: str) -> dict:
        """Verify token with auth service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/verify-token",
                    json={"token": token},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        return data
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
        except httpx.RequestError as e:
            logger.error(f"Auth service communication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        # Get token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        user_data = await self.verify_token(token)
        
        # Add user data to request state
        request.state.user = user_data
        
        response = await call_next(request)
        return response