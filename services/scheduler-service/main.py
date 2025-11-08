from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from contextlib import asynccontextmanager
import logging
import httpx
from datetime import datetime

from config import settings
from app.api import routes
from app.db.session import engine, init_db
from app.services.scheduler_service import SchedulerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    init_db(engine)
    scheduler.start()
    logger.info("Scheduler started")
    yield
    scheduler.shutdown()
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

# Store scheduler in app state
app.state.scheduler = scheduler

app.include_router(routes.router, prefix="/api/v1/schedules", tags=["schedules"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "scheduler_running": scheduler.running
    }