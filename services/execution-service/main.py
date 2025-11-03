from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Dict, Set
import asyncio
import json
import logging

from config import settings
from app.api import routes
from app.db.session import engine, init_db, get_db
from app.models.execution import Execution, ExecutionStatus
from app.schemas.execution import ExecutionCreate, ExecutionResponse
from app.core.events import event_publisher
from app.workers.celery_worker import celery_app
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.correlation_middleware import CorrelationMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, execution_id: int, websocket: WebSocket):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        self.active_connections[execution_id].add(websocket)
        logger.info(f"WebSocket connected for execution {execution_id}")
    
    def disconnect(self, execution_id: int, websocket: WebSocket):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
        logger.info(f"WebSocket disconnected for execution {execution_id}")
    
    async def broadcast(self, execution_id: int, message: dict):
        if execution_id in self.active_connections:
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    init_db(engine)
    await event_publisher.connect()
    yield
    await event_publisher.disconnect()
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

app.include_router(routes.router, prefix="/api/v1/executions", tags=["executions"])

@app.websocket("/ws/executions/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: int):
    await manager.connect(execution_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Keep connection alive
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(execution_id, websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}