from __future__ import annotations
from typing import Any
from datetime import datetime, timezone


class ClientHandoverPackage:
    """Contains all deliverables, guides, training sessions, and activated services (BR-036-002)."""

    def __init__(
        self,
        documentation: dict[str, str],
        training: dict[str, Any],
        warranty: dict[str, Any],
        support: dict[str, Any],
        deliverables: list[dict[str, Any]],
        limitations: list[str],
    ) -> None:
        self.documentation = dict(documentation or {})
        self.training = dict(training or {})
        self.warranty = dict(warranty or {})
        self.support = dict(support or {})
        self.deliverables = list(deliverables or [])
        self.limitations = list(limitations or [])

    def summary(self) -> dict[str, Any]:
        return {
            "has_user_guide": "User Documentation" in self.documentation,
            "has_admin_guide": "Administrator Guide" in self.documentation,
            "deliverable_count": len(self.deliverables),
            "warranty_scope": self.warranty.get("scope", "None"),
            "support_sla": self.support.get("sla", "None"),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "documentation": dict(self.documentation),
            "training": dict(self.training),
            "warranty": dict(self.warranty),
            "support": dict(self.support),
            "deliverables": list(self.deliverables),
            "limitations": list(self.limitations),
        }


class ClientAcceptance:
    """Tracks status, comments, conditions, and approvals of client acceptance (BR-036-003)."""

    ALLOWED_STATUSES = {
        "Draft",
        "Ready for Delivery",
        "Delivered",
        "Under Review",
        "Accepted",
        "Accepted with Conditions",
        "Rejected",
        "Closed",
    }

    def __init__(
        self,
        status: str,
        reviewer: str,
        comments: str = "",
        conditions: list[str] | None = None,
        approval_date: str | None = None,
    ) -> None:
        if status not in self.ALLOWED_STATUSES:
            raise ValueError(f"Invalid status: {status}. Allowed: {self.ALLOWED_STATUSES}")
        if not reviewer:
            raise ValueError("Reviewer is required.")

        self.status = status
        self.reviewer = reviewer
        self.comments = comments
        self.conditions = list(conditions or [])
        self.approval_date = approval_date

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reviewer": self.reviewer,
            "has_conditions": len(self.conditions) > 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reviewer": self.reviewer,
            "comments": self.comments,
            "conditions": list(self.conditions),
            "approval_date": self.approval_date,
        }


class ProjectClosureReport:
    """Consolidated document confirming final handover, active status, and executive sign-off."""

    def __init__(
        self,
        report_id: str,
        project_id: str,
        closure_summary: str,
        acceptance_result: dict[str, Any],
        archived_assets: list[str],
        knowledge_registered: list[str],
        warranty_activated: dict[str, Any],
        support_activated: dict[str, Any],
        executive_approval: dict[str, Any],
        closed_at: str | None = None,
    ) -> None:
        if not report_id:
            raise ValueError("Report ID is required.")
        if not project_id:
            raise ValueError("Project ID is required.")
        exec_status = str(executive_approval.get("status", "")).upper()
        if not executive_approval or exec_status != "APPROVED":
            raise ValueError("Executive approval is mandatory before final closure (BR-036-010).")

        self.report_id = report_id
        self.project_id = project_id
        self.closure_summary = closure_summary
        self.acceptance_result = dict(acceptance_result or {})
        self.archived_assets = list(archived_assets or [])
        self.knowledge_registered = list(knowledge_registered or [])
        self.warranty_activated = dict(warranty_activated or {})
        self.support_activated = dict(support_activated or {})
        self.executive_approval = dict(executive_approval or {})
        self.closed_at = closed_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "acceptance_status": self.acceptance_result.get("status"),
            "archived_asset_count": len(self.archived_assets),
            "knowledge_item_count": len(self.knowledge_registered),
            "closed_at": self.closed_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "closure_summary": self.closure_summary,
            "acceptance_result": dict(self.acceptance_result),
            "archived_assets": list(self.archived_assets),
            "knowledge_registered": list(self.knowledge_registered),
            "warranty_activated": dict(self.warranty_activated),
            "support_activated": dict(self.support_activated),
            "executive_approval": dict(self.executive_approval),
            "closed_at": self.closed_at,
        }
