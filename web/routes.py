from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query


def get_web_routes(controller: Any) -> APIRouter:
    """Page navigation and assistant conversation routes."""
    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "Executive Web Console"}

    @router.post("/api/converse")
    def converse_with_assistant(
        message: str = Query(..., description="User voice/text input command"),
    ) -> dict[str, Any]:
        """Routes natural-language commands to the AI assistant."""
        if not controller.ai_assistant:
            raise HTTPException(
                status_code=503,
                detail="AI Executive Assistant is currently offline.",
            )
        try:
            response_text = controller.ai_assistant.converse(message)
            return {"response": response_text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
