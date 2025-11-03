from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from app.api import routes
from app.db.session import engine, init_db
from app.core.events import event_publisher, event_consumer
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware
from shared.middleware.auth_middleware import AuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    init_db(engine)
    await event_publisher.connect()
    await event_consumer.start()
    yield
    await event_publisher.disconnect()
    await event_consumer.stop()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(LoggingMiddleware)

auth_middleware = AuthMiddleware(settings.AUTH_SERVICE_URL)

app.include_router(routes.router, prefix="/api/v1/scripts", tags=["scripts"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.get("/ready")
async def readiness_check():
    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}