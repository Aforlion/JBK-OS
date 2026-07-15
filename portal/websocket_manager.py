from __future__ import annotations

import json
from typing import Any


class PortalWebSocketManager:
    """Manages active WebSockets connections specifically for client workspaces."""

    def __init__(self) -> None:
        # Maps client_id -> list of active websockets
        self.active_connections: dict[str, list[Any]] = {}

    async def connect(self, client_id: str, websocket: Any) -> None:
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, client_id: str, websocket: Any) -> None:
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_to_client(self, client_id: str, message: dict[str, Any]) -> None:
        """Pushes real-time updates directly to a specific client's portal session."""
        if client_id not in self.active_connections:
            return

        payload = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections[client_id]:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        # Cleanup disconnected clients
        for conn in dead_connections:
            self.disconnect(client_id, conn)
