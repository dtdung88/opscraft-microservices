from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import httpx
import logging

from config import settings
from app.api import routes
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(routes.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.get("/stats")
async def get_system_stats():
    """Aggregate stats from all services"""
    stats = {}
    
    services = [
        ("auth", settings.AUTH_SERVICE_URL),
        ("script", settings.SCRIPT_SERVICE_URL),
        ("execution", settings.EXECUTION_SERVICE_URL),
        ("secret", settings.SECRET_SERVICE_URL)
    ]
    
    async with httpx.AsyncClient() as client:
        for name, url in services:
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                stats[name] = response.json()
            except Exception as e:
                stats[name] = {"status": "error", "error": str(e)}
    
    return stats