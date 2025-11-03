from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Callable, Dict
import asyncio

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers: Dict[str, KafkaConsumer] = {}
        self.handlers: Dict[str, list] = {}
    
    async def connect_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info("Kafka producer connected")
        except KafkaError as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            raise
    
    async def publish(self, topic: str, event: dict, key: str = None):
        """Publish event to topic"""
        if not self.producer:
            raise RuntimeError("Producer not connected")
        
        try:
            future = self.producer.send(
                topic,
                value=event,
                key=key.encode('utf-8') if key else None
            )
            
            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Event published to {topic} "
                f"partition={record_metadata.partition} "
                f"offset={record_metadata.offset}"
            )
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    async def subscribe(self, topic: str, group_id: str, handler: Callable):
        """Subscribe to topic with handler"""
        if topic not in self.consumers:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    enable_auto_commit=True
                )
                self.consumers[topic] = consumer
                logger.info(f"Subscribed to topic: {topic}")
            except KafkaError as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")
                raise
        
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
    
    async def start_consuming(self, topic: str):
        """Start consuming messages from topic"""
        if topic not in self.consumers:
            raise ValueError(f"Not subscribed to topic: {topic}")
        
        consumer = self.consumers[topic]
        
        try:
            for message in consumer:
                event = message.value
                logger.debug(f"Received event from {topic}: {event}")
                
                # Call all handlers for this topic
                for handler in self.handlers.get(topic, []):
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
    
    async def close(self):
        """Close all connections"""
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        logger.info("Event bus closed")