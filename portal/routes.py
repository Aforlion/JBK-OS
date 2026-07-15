from __future__ import annotations

from typing import Any
from fastapi import APIRouter


def get_portal_routes(controller: Any) -> APIRouter:
    """Base web portal health and route navigation handlers."""
    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "Client Portal Workspace"}

    return router
