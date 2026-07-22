from fastapi import WebSocket
import asyncio
from core.events import EventEmitter, AppEvent, EventKind

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

class WebSocketEventEmitter:
    """Implements EventEmitter protocol to bridge sync downloader callbacks to WebSockets."""
    def __init__(self, manager: ConnectionManager, loop: asyncio.AbstractEventLoop):
        self.manager = manager
        self.loop = loop

    def emit(self, event: AppEvent) -> None:
        ws_msg = {
            "type": event.kind.value,
            "task_id": event.task_id,
            "payload": event.payload
        }
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast(ws_msg),
            self.loop
        )
