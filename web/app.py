from __future__ import annotations

from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from web.routes import get_web_routes
from web.dashboard_api import get_dashboard_api
from web.websocket_manager import WebSocketManager


def create_app(controller: Any) -> FastAPI:
    """FastAPI Application factory initializing routes, cors, and websockets."""
    app = FastAPI(
        title="JBK OS Executive Console API",
        version="1.0.0",
        description="Stateless REST & WS presentation layer for JBK-OS.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    import time
    from fastapi import Request

    @app.middleware("http")
    async def track_metrics_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        
        path = request.url.path
        if path not in ("/health", "/ws", "/favicon.ico") and not path.startswith("/static"):
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            if hasattr(controller, "monitoring_engine") and controller.monitoring_engine:
                controller.monitoring_engine.record_metric(
                    engine_name="WebServer",
                    execution_time_ms=duration_ms,
                    success=(response.status_code < 500)
                )
        return response

    ws_manager = WebSocketManager()

    # Mount routes
    app.include_router(get_web_routes(controller))
    app.include_router(get_dashboard_api(controller))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Active push subscription connection endpoint."""
        await ws_manager.connect(websocket)
        try:
            while True:
                # Receive events (keepalive, actions)
                data = await websocket.receive_text()
                # Respond or echo if needed
                await websocket.send_text(f"ACK: {data}")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception:
            ws_manager.disconnect(websocket)

    # Attach WebSocket manager to application state
    app.state.ws_manager = ws_manager

    return app
