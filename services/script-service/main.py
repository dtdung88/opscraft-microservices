from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app

from config import settings
from app.api import routes
from app.db.session import engine, init_db
from app.core.events import event_publisher, event_consumer
from app.core.metrics import init_metrics
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware
from shared.middleware.auth_middleware import AuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    init_db(engine)
    await event_publisher.connect()
    await event_consumer.start()
    init_metrics()
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

# Auth middleware for protected routes
auth_middleware = AuthMiddleware(settings.AUTH_SERVICE_URL)

app.include_router(routes.router, prefix="/api/v1/scripts", tags=["scripts"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION
    }

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