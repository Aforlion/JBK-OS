from __future__ import annotations

from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from portal.routes import get_portal_routes
from portal.workspace_controller import get_portal_api
from portal.websocket_manager import PortalWebSocketManager


def create_portal_app(controller: Any) -> FastAPI:
    """FastAPI Application factory initializing client portal endpoints and websockets."""
    app = FastAPI(
        title="JBK OS Client Portal API",
        version="1.0.0",
        description="Presentation-only secure client portal dashboard.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ws_manager = PortalWebSocketManager()

    # Mount routers
    app.include_router(get_portal_routes(controller))
    app.include_router(get_portal_api(controller))

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
        """Active client portal socket connection mapping."""
        await ws_manager.connect(client_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"WORKSPACE-ACK: {data}")
        except WebSocketDisconnect:
            ws_manager.disconnect(client_id, websocket)
        except Exception:
            ws_manager.disconnect(client_id, websocket)

    app.state.ws_manager = ws_manager

    return app
