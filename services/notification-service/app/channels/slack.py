import httpx
from typing import List, Optional
import logging
from time import time

logger = logging.getLogger(__name__)

class SlackChannel:
    def __init__(self, webhook_url: str, bot_token: Optional[str] = None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
    
    async def send(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "OpsCraft Bot",
        icon_emoji: str = ":robot_face:",
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """Send Slack notification"""
        try:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji
            }
            
            if channel:
                payload["channel"] = channel
            
            if attachments:
                payload["attachments"] = attachments
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack message sent successfully")
                    return True
                else:
                    logger.error(f"Slack API error: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    async def send_rich_message(
        self,
        title: str,
        message: str,
        color: str = "good",
        fields: Optional[List[dict]] = None,
        actions: Optional[List[dict]] = None
    ) -> bool:
        """Send rich formatted Slack message"""
        attachment = {
            "color": color,
            "title": title,
            "text": message,
            "footer": "OpsCraft",
            "ts": int(time())
        }
        
        if fields:
            attachment["fields"] = fields
        
        if actions:
            attachment["actions"] = actions
        
        return await self.send("", attachments=[attachment])
    
    async def send_execution_notification(
        self,
        script_name: str,
        status: str,
        user: str,
        duration: str,
        execution_url: str
    ) -> bool:
        """Send script execution notification"""
        color = "good" if status == "success" else "danger"
        
        fields = [
            {"title": "Script", "value": script_name, "short": True},
            {"title": "Status", "value": status.upper(), "short": True},
            {"title": "User", "value": user, "short": True},
            {"title": "Duration", "value": duration, "short": True}
        ]
        
        actions = [
            {
                "type": "button",
                "text": "View Logs",
                "url": execution_url,
                "style": "primary"
            }
        ]
        
        return await self.send_rich_message(
            title=f"Script Execution {status.title()}",
            message=f"Script '{script_name}' has completed",
            color=color,
            fields=fields,
            actions=actions
        )