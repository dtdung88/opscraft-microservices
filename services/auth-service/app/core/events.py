"""Event publishing for auth service."""
import json
import logging
from typing import Any, Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Kafka event publisher with retry and error handling."""

    def __init__(self) -> None:
        self.producer: Optional[KafkaProducer] = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize Kafka producer with production settings."""
        if self._connected:
            return

        try:
            self.producer = await KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
                compression_type="gzip",
                linger_ms=10,
                batch_size=16384,
                request_timeout_ms=30000,
            )
            self._connected = True
            logger.info("Kafka producer connected successfully")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    async def publish(
        self,
        topic: str,
        event: dict[str, Any],
        key: Optional[str] = None,
    ) -> bool:
        """Publish event to Kafka topic."""
        if not self.producer:
            logger.warning("Kafka producer not initialized, skipping event")
            return False

        try:
            future = await self.producer.send(topic, value=event, key=key)
            record_metadata = await future.get(timeout=10)
            logger.debug(
                f"Event published to {topic} "
                f"partition={record_metadata.partition} "
                f"offset={record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            return False

    async def disconnect(self) -> None:
        """Close Kafka producer."""
        if self.producer:
            await self.producer.flush(timeout=5)
            await self.producer.close(timeout=5)
            self._connected = False
            logger.info("Kafka producer disconnected")


event_publisher = EventPublisher()