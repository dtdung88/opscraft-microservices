import httpx
import logging
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

async def send_approval_notification(approval: Any):
    """Send notification about new approval request"""
    
    notification_data = {
        "type": "approval_request",
        "title": f"Approval Required: {approval.action}",
        "message": f"User {approval.requester} requests approval for {approval.resource_type}",
        "data": {
            "approval_id": approval.id,
            "requester": approval.requester,
            "resource": f"{approval.resource_type}/{approval.resource_id}",
            "action": approval.action,
            "reason": approval.reason
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications/broadcast",
                json=notification_data,
                timeout=5.0
            )
    except Exception as e:
        logger.error(f"Failed to send approval notification: {e}")