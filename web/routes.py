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

    @router.get("/api/verify-gemini")
    def verify_gemini_integration() -> dict[str, Any]:
        """Runs a live verification request against the real Gemini API via the adapter."""
        from core.ai_provider import GeminiAdapter, AICapability
        from core.ai_gateway import AIRequest
        
        adapter = GeminiAdapter()
        request = AIRequest(
            capability=AICapability.CHAT,
            prompt="Reply in exactly one word: VERIFIED",
            system_context="You are a validation bot.",
            temperature=0.0,
            max_tokens=100
        )
        try:
            res = adapter.generate(request)
            # Remove any raw prompt contents from response metadata to ensure no leakage
            return {
                "success": res.get("success", False),
                "model": res.get("model", "none"),
                "latency_ms": res.get("latency_ms", 0),
                "token_usage": res.get("token_usage", {}),
                "verified": "VERIFIED" in (res.get("content") or "").upper()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini API verification failed: {e}")


    return router
