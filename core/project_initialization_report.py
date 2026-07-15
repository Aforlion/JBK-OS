from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class ProjectInitializationReport:
    def __init__(
        self,
        report_id: str,
        project_id: str,
        proposal_id: str,
        decision_id: str,
        estimate_id: str,
        blueprint_id: str,
        discovery_plan_id: str,
        opportunity_id: str | None,
        client_name: str,
        client_organization: str,
        project_title: str,
        project_description: str,
        coordinator_id: str,
        initial_work_orders: list[dict[str, Any]],
        status: str,
        created_at: str | None = None,
    ) -> None:
        self.report_id = report_id
        self.project_id = project_id
        self.proposal_id = proposal_id
        self.decision_id = decision_id
        self.estimate_id = estimate_id
        self.blueprint_id = blueprint_id
        self.discovery_plan_id = discovery_plan_id
        self.opportunity_id = opportunity_id
        self.client_name = client_name
        self.client_organization = client_organization
        self.project_title = project_title
        self.project_description = project_description
        self.coordinator_id = coordinator_id
        self.initial_work_orders = initial_work_orders or []
        self.status = status or "INITIALIZED"
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "proposal_id": self.proposal_id,
            "project_title": self.project_title,
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "proposal_id": self.proposal_id,
            "decision_id": self.decision_id,
            "estimate_id": self.estimate_id,
            "blueprint_id": self.blueprint_id,
            "discovery_plan_id": self.discovery_plan_id,
            "opportunity_id": self.opportunity_id,
            "client_name": self.client_name,
            "client_organization": self.client_organization,
            "project_title": self.project_title,
            "project_description": self.project_description,
            "coordinator_id": self.coordinator_id,
            "initial_work_orders": [dict(wo) for wo in self.initial_work_orders],
            "status": self.status,
            "created_at": self.created_at,
        }
