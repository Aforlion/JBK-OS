from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Header, HTTPException, status


def get_portal_api(controller: Any) -> APIRouter:
    """Returns the APIRouter mounting client portal workspace endpoints."""
    router = APIRouter(prefix="/api/portal")

    @router.get("/workspace/{client_id}")
    def read_workspace(
        client_id: str,
        x_authenticated_client: str = Header(..., description="Mock auth header payload"),
    ) -> dict[str, Any]:
        """Loads client workspace after validating client isolation boundaries."""
        try:
            vm = controller.load_workspace(client_id, x_authenticated_client)
            return vm.to_dict()
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load client workspace: {e}",
            )

    @router.post("/workspace/{client_id}/approve/proposal/{proposal_id}")
    def approve_proposal(
        client_id: str,
        proposal_id: str,
        x_authenticated_client: str = Header(..., description="Mock auth header payload"),
        approver: str = "Client Approver",
    ) -> dict[str, Any]:
        """Approve proposal."""
        if client_id != x_authenticated_client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Isolation breach.")
        return controller.approve_proposal(client_id, proposal_id, approver)

    @router.post("/workspace/{client_id}/approve/milestone/{project_id}")
    def approve_milestone(
        client_id: str,
        project_id: str,
        milestone_title: str,
        x_authenticated_client: str = Header(..., description="Mock auth header payload"),
        approver: str = "Client Approver",
    ) -> dict[str, Any]:
        """Approve milestone."""
        if client_id != x_authenticated_client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Isolation breach.")
        return controller.approve_milestone(client_id, project_id, milestone_title, approver)

    @router.post("/workspace/{client_id}/support")
    def submit_support(
        client_id: str,
        payload: dict[str, str],
        x_authenticated_client: str = Header(..., description="Mock auth header payload"),
    ) -> dict[str, Any]:
        """Submit support ticket."""
        if client_id != x_authenticated_client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Isolation breach.")
        return controller.submit_support_request(client_id, payload.get("title", ""), payload.get("description", ""))

    @router.post("/workspace/{client_id}/feedback")
    def submit_feedback(
        client_id: str,
        payload: dict[str, Any],
        x_authenticated_client: str = Header(..., description="Mock auth header payload"),
    ) -> dict[str, Any]:
        """Submit client satisfaction feedback."""
        if client_id != x_authenticated_client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Isolation breach.")
        return controller.submit_feedback(client_id, float(payload.get("score", 5.0)), payload.get("comments", ""))

    return router
