from __future__ import annotations

import json
from typing import Any


class WebSocketManager:
    """Manages active WebSockets connections to push real-time updates to the UI."""

    def __init__(self) -> None:
        self.active_connections: list[Any] = []

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: Any) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: Any) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast status update payload to all connected clients."""
        payload = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        # Cleanup disconnected clients
        for conn in dead_connections:
            self.disconnect(conn)
