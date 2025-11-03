from kafka import KafkaProducer, KafkaConsumer
import json
import logging
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self):
        self.producer = None
    
    async def connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer connected")
        except Exception as e:
            logger.error(f"Kafka connection failed: {e}")
    
    async def publish(self, topic: str, event: dict):
        if self.producer:
            self.producer.send(topic, value=event)
            self.producer.flush()
    
    async def disconnect(self):
        if self.producer:
            self.producer.close()

class EventConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False
    
    async def start(self):
        self.running = True
        # Start consuming user events
        asyncio.create_task(self._consume_events())
    
    async def _consume_events(self):
        try:
            self.consumer = KafkaConsumer(
                'user-events',
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='script-service'
            )
            
            while self.running:
                for message in self.consumer:
                    event = message.value
                    await self._handle_event(event)
        except Exception as e:
            logger.error(f"Consumer error: {e}")
    
    async def _handle_event(self, event: dict):
        event_type = event.get('event_type')
        logger.info(f"Received event: {event_type}")
        # Handle events as needed
    
    async def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()

event_publisher = EventPublisher()
event_consumer = EventConsumer()