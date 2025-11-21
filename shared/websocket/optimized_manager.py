from fastapi import WebSocket
from typing import Dict, Set, List
import asyncio
from collections import defaultdict

class OptimizedConnectionManager:
    """Optimized WebSocket connection management"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.user_channels: Dict[str, Set[str]] = defaultdict(set)
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self._broadcast_queue = asyncio.Queue(maxsize=10000)
        self._broadcast_task = None
    
    async def start(self):
        """Start background broadcast worker"""
        self._broadcast_task = asyncio.create_task(self._broadcast_worker())
    
    async def _broadcast_worker(self):
        """Background worker for batch broadcasting"""
        while True:
            messages = []
            try:
                # Collect messages for batch processing
                while len(messages) < 100:  # Batch size
                    try:
                        msg = await asyncio.wait_for(
                            self._broadcast_queue.get(), 
                            timeout=0.1
                        )
                        messages.append(msg)
                    except asyncio.TimeoutError:
                        break
                
                if messages:
                    await self._broadcast_batch(messages)
            
            except Exception as e:
                logger.error(f"Broadcast worker error: {e}")
    
    async def _broadcast_batch(self, messages: List[tuple]):
        """Send batch of messages efficiently"""
        # Group messages by channel
        channel_messages = defaultdict(list)
        for channel, message in messages:
            channel_messages[channel].append(message)
        
        # Broadcast to each channel
        for channel, msgs in channel_messages.items():
            if channel in self.active_connections:
                # Send all messages to all connections in parallel
                tasks = []
                for connection in self.active_connections[channel]:
                    for msg in msgs:
                        tasks.append(connection.send_json(msg))
                
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, channel: str, message: dict):
        """Queue message for broadcasting"""
        try:
            self._broadcast_queue.put_nowait((channel, message))
        except asyncio.QueueFull:
            logger.warning("Broadcast queue full, dropping message")