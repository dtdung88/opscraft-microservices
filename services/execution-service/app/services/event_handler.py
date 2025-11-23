"""Event handling for execution service."""
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from kafka import KafkaProducer

from config import settings

logger = logging.getLogger(__name__)


class ExecutionEventHandler:
    """Handles publishing and processing of execution events."""

    TOPIC = "execution-events"

    def __init__(self) -> None:
        self.producer: KafkaProducer | None = None

    async def connect(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.producer = await KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
            )
            logger.info("Execution event handler connected")
        except Exception as e:
            logger.error(f"Failed to connect event handler: {e}")

    def _create_event(
        self,
        event_type: str,
        execution_id: int,
        **data: Any,
    ) -> dict[str, Any]:
        """Create standardized event payload."""
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id,
            **data,
        }

    async def publish_execution_started(
        self,
        execution_id: int,
        script_id: int,
        script_name: str,
        executed_by: str,
        parameters: dict[str, Any],
    ) -> None:
        """Publish execution started event."""
        event = self._create_event(
            "execution.started",
            execution_id,
            script_id=script_id,
            script_name=script_name,
            executed_by=executed_by,
            parameters=parameters,
        )
        await self._publish(event)

    async def publish_execution_completed(
        self,
        execution_id: int,
        script_id: int,
        status: str,
        exit_code: int,
        duration_ms: int,
    ) -> None:
        """Publish execution completed event."""
        event = self._create_event(
            "execution.completed",
            execution_id,
            script_id=script_id,
            status=status,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )
        await self._publish(event)

    async def publish_execution_failed(
        self,
        execution_id: int,
        script_id: int,
        error: str,
    ) -> None:
        """Publish execution failed event."""
        event = self._create_event(
            "execution.failed",
            execution_id,
            script_id=script_id,
            error=error,
        )
        await self._publish(event)

    async def _publish(self, event: dict[str, Any]) -> None:
        """Internal publish method."""
        if not self.producer:
            logger.warning("Producer not connected")
            return

        try:
            await self.producer.send(self.TOPIC, value=event)
            await self.producer.flush()
            logger.debug(f"Published: {event['event_type']}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def disconnect(self) -> None:
        """Close producer."""
        if self.producer:
            await self.producer.close()


execution_event_handler = ExecutionEventHandler()