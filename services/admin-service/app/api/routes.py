from fastapi import APIRouter, Depends, HTTPException, status, Request
import httpx
from typing import List, Dict
import logging

from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

async def verify_admin(request: Request):
    user = request.state.user
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

@router.get("/users")
async def list_users(
    admin: dict = Depends(verify_admin)
):
    """List all users from auth service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/users",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )

@router.get("/stats")
async def get_system_stats(
    admin: dict = Depends(verify_admin)
):
    """Get aggregated system statistics"""
    stats = {
        "services": {},
        "summary": {
            "total_users": 0,
            "total_scripts": 0,
            "total_executions": 0,
            "total_secrets": 0
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Auth service stats
        try:
            response = await client.get(f"{settings.AUTH_SERVICE_URL}/api/v1/auth/stats")
            if response.status_code == 200:
                auth_stats = response.json()
                stats["services"]["auth"] = auth_stats
                stats["summary"]["total_users"] = auth_stats.get("total_users", 0)
        except:
            stats["services"]["auth"] = {"status": "unavailable"}
        
        # Script service stats
        try:
            response = await client.get(f"{settings.SCRIPT_SERVICE_URL}/api/v1/scripts/stats")
            if response.status_code == 200:
                script_stats = response.json()
                stats["services"]["script"] = script_stats
                stats["summary"]["total_scripts"] = script_stats.get("total_scripts", 0)
        except:
            stats["services"]["script"] = {"status": "unavailable"}
        
        # Execution service stats
        try:
            response = await client.get(f"{settings.EXECUTION_SERVICE_URL}/api/v1/executions/stats")
            if response.status_code == 200:
                exec_stats = response.json()
                stats["services"]["execution"] = exec_stats
                stats["summary"]["total_executions"] = exec_stats.get("total_executions", 0)
        except:
            stats["services"]["execution"] = {"status": "unavailable"}
        
        # Secret service stats
        try:
            response = await client.get(f"{settings.SECRET_SERVICE_URL}/api/v1/secrets/stats")
            if response.status_code == 200:
                secret_stats = response.json()
                stats["services"]["secret"] = secret_stats
                stats["summary"]["total_secrets"] = secret_stats.get("total_secrets", 0)
        except:
            stats["services"]["secret"] = {"status": "unavailable"}
    
    return stats

@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    admin: dict = Depends(verify_admin)
):
    """Update user role"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/users/{user_id}/role",
                json={"role": role}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )