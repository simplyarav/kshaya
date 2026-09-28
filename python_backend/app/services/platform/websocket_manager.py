from fastapi import WebSocket
from typing import List, Dict
import asyncio
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_job_update(self, job_id: int, status: str, progress: int = 0, details: dict = None):
        if details is None:
            details = {}
            
        message = {
            "type": "JOB_UPDATE",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "details": details
        }
        json_msg = json.dumps(message)
        
        # Create a copy of the list to safely iterate
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json_msg)
            except Exception:
                self.disconnect(connection)

# Global singleton
ws_manager = WebSocketManager()
