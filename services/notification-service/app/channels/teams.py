import httpx
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TeamsChannel:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(
        self,
        title: str,
        message: str,
        theme_color: str = "0076D7",
        sections: Optional[List[dict]] = None,
        actions: Optional[List[dict]] = None
    ) -> bool:
        """Send Microsoft Teams notification"""
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": theme_color,
                "title": title,
                "text": message
            }
            
            if sections:
                payload["sections"] = sections
            
            if actions:
                payload["potentialAction"] = actions
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Teams message sent successfully")
                    return True
                else:
                    logger.error(f"Teams API error: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False
    
    async def send_execution_notification(
        self,
        script_name: str,
        status: str,
        user: str,
        duration: str,
        execution_url: str
    ) -> bool:
        """Send script execution notification"""
        theme_color = "28A745" if status == "success" else "DC3545"
        
        sections = [{
            "facts": [
                {"name": "Script", "value": script_name},
                {"name": "Status", "value": status.upper()},
                {"name": "User", "value": user},
                {"name": "Duration", "value": duration}
            ]
        }]
        
        actions = [{
            "@type": "OpenUri",
            "name": "View Logs",
            "targets": [{"os": "default", "uri": execution_url}]
        }]
        
        return await self.send(
            title=f"Script Execution {status.title()}",
            message=f"Script '{script_name}' execution completed",
            theme_color=theme_color,
            sections=sections,
            actions=actions
        )