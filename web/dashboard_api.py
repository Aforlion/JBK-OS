from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status


def get_dashboard_api(controller: Any) -> APIRouter:
    """Returns the APIRouter mounting RESTful Console API endpoints."""
    router = APIRouter(prefix="/api/dashboard")

    @router.get("/")
    def read_dashboard() -> dict[str, Any]:
        """Loads structured view model dashboard."""
        try:
            vm = controller.load_dashboard()
            return vm.to_dict()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load dashboard: {e}",
            )

    @router.post("/refresh")
    def refresh_dashboard() -> dict[str, Any]:
        """Manually refresh dashboard layout."""
        try:
            vm = controller.load_dashboard()
            return {"status": "success", "dashboard": vm.to_dict()}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh dashboard: {e}",
            )

    @router.get("/projects")
    def read_projects() -> list[dict[str, Any]]:
        """Fetch list of project cards."""
        try:
            cards = controller.load_projects()
            return [c.to_dict() for c in cards]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    @router.post("/actions/{action_name}")
    def execute_action(action_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Triggers a quick action endpoint."""
        res = controller.quick_action(action_name, payload)
        if not res.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("error", "Action failed"),
            )
        return res

    @router.get("/search")
    def global_search(q: str) -> list[dict[str, Any]]:
        """Perform a global query search."""
        return controller.search(q)

    @router.get("/metrics")
    def get_operational_metrics() -> dict[str, Any]:
        """Fetch real-time operational telemetry (response times, AI stats, error rates)."""
        if not hasattr(controller, "monitoring_engine") or not controller.monitoring_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Monitoring engine is offline."
            )
            
        web_stats = controller.monitoring_engine.query_metrics("WebServer", window_hours=24)
        ai_stats = controller.monitoring_engine.query_metrics("AIGateway", window_hours=24)
        
        error_rate = 0.0
        if web_stats.get("total_runs", 0) > 0:
            error_rate = 100.0 - web_stats.get("success_rate_pct", 100.0)
            
        return {
            "average_response_time_ms": web_stats.get("average_execution_time_ms", 0.0),
            "ai_latency_ms": ai_stats.get("average_execution_time_ms", 0.0),
            "requests_per_day": web_stats.get("total_runs", 0),
            "token_usage": ai_stats.get("total_ai_tokens", 0),
            "estimated_ai_cost": ai_stats.get("total_ai_cost", 0.0),
            "error_rate_pct": round(error_rate, 2)
        }

    return router
