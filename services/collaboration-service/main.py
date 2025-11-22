"""
Collaboration Service - Real-time Script Collaboration
Port: 8012
Provides real-time collaborative editing with operational transformation.
"""
import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SERVICE_NAME: str = "collaboration-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8012
    REDIS_URL: str = "redis://redis:6379/9"
    MAX_USERS_PER_SESSION: int = 10
    SESSION_TIMEOUT_SECONDS: int = 3600
    HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


class OperationType(str, Enum):
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"


@dataclass
class Operation:
    """Represents an edit operation for OT."""

    type: OperationType
    position: int
    content: str = ""
    length: int = 0
    user_id: str = ""
    timestamp: float = field(default_factory=time.time)
    revision: int = 0


@dataclass
class CursorPosition:
    """User cursor position."""

    user_id: str
    username: str
    line: int
    column: int
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    color: str = "#3b82f6"


@dataclass
class CollaborationSession:
    """Represents a collaborative editing session."""

    script_id: int
    content: str = ""
    revision: int = 0
    connections: dict[str, WebSocket] = field(default_factory=dict)
    cursors: dict[str, CursorPosition] = field(default_factory=dict)
    history: list[Operation] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


class OperationalTransform:
    """Operational Transformation engine for conflict resolution."""

    @staticmethod
    def transform(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """Transform two concurrent operations."""
        if op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
            if op1.position <= op2.position:
                new_op2 = Operation(
                    type=op2.type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    user_id=op2.user_id,
                    revision=op2.revision,
                )
                return op1, new_op2
            else:
                new_op1 = Operation(
                    type=op1.type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    user_id=op1.user_id,
                    revision=op1.revision,
                )
                return new_op1, op2

        if op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
            if op1.position >= op2.position + op2.length:
                new_op1 = Operation(
                    type=op1.type,
                    position=op1.position - op2.length,
                    length=op1.length,
                    user_id=op1.user_id,
                    revision=op1.revision,
                )
                return new_op1, op2
            elif op2.position >= op1.position + op1.length:
                new_op2 = Operation(
                    type=op2.type,
                    position=op2.position - op1.length,
                    length=op2.length,
                    user_id=op2.user_id,
                    revision=op2.revision,
                )
                return op1, new_op2

        if op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            if op1.position <= op2.position:
                new_op2 = Operation(
                    type=op2.type,
                    position=op2.position + len(op1.content),
                    length=op2.length,
                    user_id=op2.user_id,
                    revision=op2.revision,
                )
                return op1, new_op2
            elif op1.position >= op2.position + op2.length:
                new_op1 = Operation(
                    type=op1.type,
                    position=op1.position - op2.length,
                    content=op1.content,
                    user_id=op1.user_id,
                    revision=op1.revision,
                )
                return new_op1, op2

        return op1, op2

    @staticmethod
    def apply(content: str, operation: Operation) -> str:
        """Apply an operation to content."""
        if operation.type == OperationType.INSERT:
            return (
                content[: operation.position]
                + operation.content
                + content[operation.position :]
            )
        elif operation.type == OperationType.DELETE:
            return (
                content[: operation.position]
                + content[operation.position + operation.length :]
            )
        return content


class CollaborationManager:
    """Manages real-time collaboration sessions."""

    def __init__(self):
        self.sessions: dict[int, CollaborationSession] = {}
        self.user_sessions: dict[str, int] = {}
        self.ot_engine = OperationalTransform()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())

    async def stop(self):
        """Stop background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_inactive_sessions(self):
        """Remove inactive sessions periodically."""
        while True:
            await asyncio.sleep(60)
            current_time = time.time()
            inactive = [
                sid
                for sid, session in self.sessions.items()
                if current_time - session.last_activity > settings.SESSION_TIMEOUT_SECONDS
                and not session.connections
            ]
            for sid in inactive:
                del self.sessions[sid]
                logger.info(f"Cleaned up inactive session: {sid}")

    def get_or_create_session(
        self, script_id: int, initial_content: str = ""
    ) -> CollaborationSession:
        """Get existing session or create new one."""
        if script_id not in self.sessions:
            self.sessions[script_id] = CollaborationSession(
                script_id=script_id,
                content=initial_content,
            )
            logger.info(f"Created new collaboration session for script {script_id}")
        return self.sessions[script_id]

    async def join_session(
        self,
        script_id: int,
        user_id: str,
        username: str,
        websocket: WebSocket,
    ) -> CollaborationSession:
        """Add user to collaboration session."""
        session = self.get_or_create_session(script_id)

        if len(session.connections) >= settings.MAX_USERS_PER_SESSION:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Session is full",
            )

        await websocket.accept()
        session.connections[user_id] = websocket
        self.user_sessions[user_id] = script_id

        colors = [
            "#ef4444", "#f97316", "#eab308", "#22c55e",
            "#14b8a6", "#3b82f6", "#8b5cf6", "#ec4899",
        ]
        color = colors[len(session.cursors) % len(colors)]
        session.cursors[user_id] = CursorPosition(
            user_id=user_id,
            username=username,
            line=0,
            column=0,
            color=color,
        )

        await self._broadcast_to_session(
            session,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "users": [
                    {"user_id": c.user_id, "username": c.username, "color": c.color}
                    for c in session.cursors.values()
                ],
            },
            exclude_user=None,
        )

        await websocket.send_json({
            "type": "session_state",
            "content": session.content,
            "revision": session.revision,
            "cursors": [
                {
                    "user_id": c.user_id,
                    "username": c.username,
                    "line": c.line,
                    "column": c.column,
                    "color": c.color,
                }
                for c in session.cursors.values()
                if c.user_id != user_id
            ],
        })

        logger.info(f"User {username} joined session for script {script_id}")
        return session

    async def leave_session(self, script_id: int, user_id: str):
        """Remove user from collaboration session."""
        if script_id not in self.sessions:
            return

        session = self.sessions[script_id]
        session.connections.pop(user_id, None)
        cursor = session.cursors.pop(user_id, None)
        self.user_sessions.pop(user_id, None)

        await self._broadcast_to_session(
            session,
            {
                "type": "user_left",
                "user_id": user_id,
                "username": cursor.username if cursor else "Unknown",
            },
            exclude_user=user_id,
        )

        logger.info(f"User {user_id} left session for script {script_id}")

    async def handle_operation(
        self,
        script_id: int,
        user_id: str,
        operation_data: dict,
    ) -> Operation:
        """Handle an edit operation with OT."""
        session = self.sessions.get(script_id)
        if not session:
            raise ValueError(f"Session not found: {script_id}")

        operation = Operation(
            type=OperationType(operation_data["type"]),
            position=operation_data["position"],
            content=operation_data.get("content", ""),
            length=operation_data.get("length", 0),
            user_id=user_id,
            revision=operation_data.get("revision", session.revision),
        )

        if operation.revision < session.revision:
            for hist_op in session.history[operation.revision :]:
                operation, _ = self.ot_engine.transform(operation, hist_op)

        session.content = self.ot_engine.apply(session.content, operation)
        session.revision += 1
        operation.revision = session.revision
        session.history.append(operation)
        session.last_activity = time.time()

        if len(session.history) > 1000:
            session.history = session.history[-500:]

        await self._broadcast_to_session(
            session,
            {
                "type": "operation",
                "operation": {
                    "type": operation.type.value,
                    "position": operation.position,
                    "content": operation.content,
                    "length": operation.length,
                    "user_id": operation.user_id,
                },
                "revision": session.revision,
            },
            exclude_user=user_id,
        )

        return operation

    async def update_cursor(
        self,
        script_id: int,
        user_id: str,
        line: int,
        column: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None,
    ):
        """Update user cursor position."""
        session = self.sessions.get(script_id)
        if not session or user_id not in session.cursors:
            return

        cursor = session.cursors[user_id]
        cursor.line = line
        cursor.column = column
        cursor.selection_start = selection_start
        cursor.selection_end = selection_end

        await self._broadcast_to_session(
            session,
            {
                "type": "cursor_update",
                "cursor": {
                    "user_id": user_id,
                    "username": cursor.username,
                    "line": line,
                    "column": column,
                    "selection_start": selection_start,
                    "selection_end": selection_end,
                    "color": cursor.color,
                },
            },
            exclude_user=user_id,
        )

    async def _broadcast_to_session(
        self,
        session: CollaborationSession,
        message: dict,
        exclude_user: Optional[str] = None,
    ):
        """Broadcast message to all session participants."""
        disconnected = []
        for uid, ws in session.connections.items():
            if uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to {uid}: {e}")
                disconnected.append(uid)

        for uid in disconnected:
            await self.leave_session(session.script_id, uid)


manager = CollaborationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    await manager.start()
    yield
    await manager.stop()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/collaborate/{script_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    script_id: int,
    user_id: str = "",
    username: str = "Anonymous",
):
    """WebSocket endpoint for real-time collaboration."""
    if not user_id:
        user_id = str(uuid.uuid4())

    try:
        session = await manager.join_session(script_id, user_id, username, websocket)

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=settings.HEARTBEAT_INTERVAL,
                )

                msg_type = data.get("type")

                if msg_type == "operation":
                    await manager.handle_operation(script_id, user_id, data["operation"])
                elif msg_type == "cursor":
                    await manager.update_cursor(
                        script_id,
                        user_id,
                        data.get("line", 0),
                        data.get("column", 0),
                        data.get("selection_start"),
                        data.get("selection_end"),
                    )
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        await manager.leave_session(script_id, user_id)


@app.get("/api/v1/collaboration/sessions/{script_id}")
async def get_session_info(script_id: int):
    """Get information about a collaboration session."""
    session = manager.sessions.get(script_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {
        "script_id": script_id,
        "revision": session.revision,
        "users": [
            {"user_id": c.user_id, "username": c.username, "color": c.color}
            for c in session.cursors.values()
        ],
        "user_count": len(session.connections),
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "active_sessions": len(manager.sessions),
    }