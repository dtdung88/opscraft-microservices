from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List
import logging

from config import settings
from app.api import routes
from app.db.session import engine, init_db, get_db
from app.models.secret import Secret
from app.models.audit import AuditLog
from app.schemas.secret import SecretCreate, SecretResponse
from app.core.encryption import EncryptionService
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    init_db(engine)
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
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

app.include_router(routes.router, prefix="/api/v1/secrets", tags=["secrets"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}