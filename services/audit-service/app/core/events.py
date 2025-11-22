from kafka import KafkaConsumer
import json
import logging
from datetime import datetime, timezone
from config import settings

logger = logging.getLogger(__name__)

class AuditEventConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False

    async def start(self):
        """Start consuming events from Kafka"""
        self.running = True
        try:
            self.consumer = KafkaConsumer(
                'user-events',
                'script-events',
                'execution-events',
                'secret-events',
                'approval-events',
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='audit-service',
                auto_offset_reset='earliest'
            )
            logger.info("Audit event consumer started")
            for message in self.consumer:
                if not self.running:
                    break
                event = message.value
                await self._process_event(event)
        except Exception as e:
            logger.error(f"Audit consumer error: {e}")

    async def _process_event(self, event: dict):
        """Process and store audit event"""
        from app.db.session import SessionLocal
        from app.models.audit import AuditLog
        db = SessionLocal()
        try:
            risk_level = self._calculate_risk_level(event)
            audit_log = AuditLog(
                event_type=event.get('event_type'),
                event_category=self._get_category(event.get('event_type')),
                action=event.get('action', 'unknown'),
                user_id=event.get('user_id'),
                username=event.get('username', 'system'),
                user_role=event.get('user_role'),
                ip_address=event.get('ip_address'),
                resource_type=event.get('resource_type', 'unknown'),
                resource_id=str(event.get('resource_id', '')),
                resource_name=event.get('resource_name'),
                service_name=event.get('service', 'unknown'),
                endpoint=event.get('endpoint'),
                http_method=event.get('http_method'),
                request_id=event.get('request_id'),
                correlation_id=event.get('correlation_id'),
                old_values=event.get('old_values'),
                new_values=event.get('new_values'),
                metadata=event.get('metadata'),
                status=event.get('status', 'success'),
                error_message=event.get('error'),
                risk_level=risk_level,
                flagged=risk_level in ['high', 'critical']
            )
            db.add(audit_log)
            db.commit()
            logger.info(f"Audit log created: {event.get('event_type')}")
        except Exception as e:
            logger.error(f"Failed to process audit event: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_category(self, event_type: str) -> str:
        if not event_type:
            return 'unknown'
        if event_type.startswith('user.'):
            return 'auth'
        elif event_type.startswith('script.'):
            return 'script'
        elif event_type.startswith('execution.'):
            return 'execution'
        elif event_type.startswith('secret.'):
            return 'secret'
        elif event_type.startswith('approval.'):
            return 'approval'
        return 'system'

    def _calculate_risk_level(self, event: dict) -> str:
        event_type = event.get('event_type', '')
        status = event.get('status', 'success')
        if any(x in event_type for x in ['delete', 'role_changed', 'secret.reveal']):
            return 'high'
        if status == 'failure':
            return 'medium'
        if 'secret' in event_type:
            return 'medium'
        return 'low'

    async def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Audit event consumer stopped")

event_consumer = AuditEventConsumer()