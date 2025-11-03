from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    service: str
    correlation_id: Optional[str] = None

class UserCreatedEvent(BaseEvent):
    user_id: int
    username: str
    email: str
    role: str
    event_type: str = "user.created"

class UserLoggedInEvent(BaseEvent):
    user_id: int
    username: str
    ip_address: Optional[str] = None
    event_type: str = "user.logged_in"

class ScriptCreatedEvent(BaseEvent):
    script_id: int
    script_name: str
    script_type: str
    created_by: str
    event_type: str = "script.created"

class ScriptUpdatedEvent(BaseEvent):
    script_id: int
    script_name: str
    updated_by: str
    changes: Dict[str, Any]
    event_type: str = "script.updated"

class ScriptDeletedEvent(BaseEvent):
    script_id: int
    script_name: str
    deleted_by: str
    event_type: str = "script.deleted"

class ExecutionStartedEvent(BaseEvent):
    execution_id: int
    script_id: int
    script_name: str
    executed_by: str
    parameters: Dict[str, Any]
    event_type: str = "execution.started"

class ExecutionCompletedEvent(BaseEvent):
    execution_id: int
    script_id: int
    status: str
    exit_code: int
    duration_seconds: float
    event_type: str = "execution.completed"

class SecretCreatedEvent(BaseEvent):
    secret_id: int
    secret_name: str
    created_by: str
    event_type: str = "secret.created"

class SecretAccessedEvent(BaseEvent):
    secret_id: int
    secret_name: str
    accessed_by: str
    execution_id: Optional[int] = None
    event_type: str = "secret.accessed"