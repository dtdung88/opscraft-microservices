from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class CollaborationManager:
    """Real-time collaboration on scripts"""
    
    def __init__(self):
        self.script_sessions: Dict[int, Set[WebSocket]] = {}
        self.user_cursors: Dict[int, Dict[str, dict]] = {}
    
    async def handle_edit(
        self,
        script_id: int,
        user_id: str,
        operation: dict
    ):
        """Handle collaborative edit operation"""
        # Operational Transform (OT) for conflict resolution
        transformed_op = self.transform_operation(
            script_id, operation
        )
        
        # Broadcast to all users except sender
        await self.broadcast_to_session(
            script_id,
            {
                "type": "edit",
                "user_id": user_id,
                "operation": transformed_op
            },
            exclude_user=user_id
        )