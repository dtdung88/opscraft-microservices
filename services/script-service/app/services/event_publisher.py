"""Event publishing utilities for script service."""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from kafka import KafkaProducer
from kafka.errors import KafkaError

from config import settings

logger = logging.getLogger(__name__)


class ScriptEventPublisher:
    """Publishes script-related events to Kafka."""

    TOPIC = "script-events"

    def __init__(self) -> None:
        self.producer: Optional[KafkaProducer] = None

    async def connect(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.producer = await KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                compression_type="gzip",
            )
            logger.info("Script event publisher connected")
        except KafkaError as e:
            logger.error(f"Failed to connect script event publisher: {e}")

    def _create_event(
        self,
        event_type: str,
        script_id: int,
        script_name: str,
        user: str,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create standardized event payload."""
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script_id": script_id,
            "script_name": script_name,
            "user": user,
            **extra,
        }

    async def publish_script_created(
        self,
        script_id: int,
        script_name: str,
        script_type: str,
        created_by: str,
    ) -> None:
        """Publish script created event."""
        event = self._create_event(
            "script.created",
            script_id,
            script_name,
            created_by,
            script_type=script_type,
        )
        await self._publish(event)

    async def publish_script_updated(
        self,
        script_id: int,
        script_name: str,
        updated_by: str,
        changes: dict[str, Any],
    ) -> None:
        """Publish script updated event."""
        event = self._create_event(
            "script.updated",
            script_id,
            script_name,
            updated_by,
            changes=changes,
        )
        await self._publish(event)

    async def publish_script_deleted(
        self,
        script_id: int,
        script_name: str,
        deleted_by: str,
    ) -> None:
        """Publish script deleted event."""
        event = self._create_event(
            "script.deleted",
            script_id,
            script_name,
            deleted_by,
        )
        await self._publish(event)

    async def _publish(self, event: dict[str, Any]) -> None:
        """Internal method to publish event."""
        if not self.producer:
            logger.warning("Producer not connected, event not published")
            return

        try:
            await self.producer.send(self.TOPIC, value=event)
            await self.producer.flush()
            logger.debug(f"Published event: {event['event_type']}")
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")

    async def disconnect(self) -> None:
        """Close producer connection."""
        if self.producer:
            await self.producer.close()
            logger.info("Script event publisher disconnected")


script_event_publisher = ScriptEventPublisher()