from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from config import settings
from app.api import routes
from app.db.session import engine, init_db
from app.core.events import event_publisher
from app.core.metrics import init_metrics
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    init_db(engine)
    await event_publisher.connect()
    init_metrics()
    
    yield
    
    # Shutdown
    await event_publisher.disconnect()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(LoggingMiddleware)

# Instrumentation
FastAPIInstrumentor.instrument_app(app)

# Routes
app.include_router(routes.router, prefix="/api/v1/auth", tags=["auth"])

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
    # Check database connection
    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}