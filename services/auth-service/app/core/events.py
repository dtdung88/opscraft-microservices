from kafka import KafkaProducer
import json
import logging
from config import settings

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self):
        self.producer = None
    
    async def connect(self):
        try:
            self.producer = await KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("Connected to Kafka")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
    
    async def publish(self, topic: str, event):
        if not self.producer:
            logger.warning("Kafka producer not initialized")
            return
        
        try:
            event_dict = event.dict() if hasattr(event, 'dict') else event
            self.producer.send(topic, value=event_dict)
            await self.producer.flush()
            logger.info(f"Published event to {topic}: {event_dict}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    async def disconnect(self):
        if self.producer:
            await self.producer.close()
            logger.info("Disconnected from Kafka")

event_publisher = EventPublisher()