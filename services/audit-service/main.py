from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from config import settings
from app.api import routes
from app.db.session import engine, init_db
from app.core.events import event_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    init_db(engine)
    await event_consumer.start()
    yield
    await event_consumer.stop()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")

app = FastAPI(
    title="Audit Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(routes.router, prefix="/api/v1/audit", tags=["audit"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "audit-service"}