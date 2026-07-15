from __future__ import annotations

from typing import Any

# Standard roles
ROLES = ("CEO", "CHIEF_OF_STAFF", "EXECUTIVE", "AI_EXECUTIVE", "CLIENT", "SUPPORT", "ADMINISTRATOR", "SERVICE_ACCOUNT")

# Standard permissions mapped to actions
ROLE_POLICIES = {
    "CEO": {
        "view_strategic_intel", "view_executive_meetings", "approve_spending", "sign_contracts",
        "hire_staff", "access_knowledge_registry", "modify_work_orders", "view_portfolio",
        "view_financials", "create_project", "trigger_quick_action",
    },
    "CHIEF_OF_STAFF": {
        "view_portfolio", "view_executive_meetings", "access_knowledge_registry", "modify_work_orders",
        "create_project", "trigger_quick_action",
    },
    "EXECUTIVE": {
        "view_portfolio", "view_executive_meetings", "access_knowledge_registry",
    },
    "AI_EXECUTIVE": {
        "execute_coding_skills", "access_repositories", "create_deliverables",
    },
    "CLIENT": {
        "view_client_workspace", "submit_support_ticket", "submit_feedback", "approve_proposal", "approve_milestone",
    },
    "SUPPORT": {
        "view_support_tickets", "resolve_support_tickets",
    },
    "ADMINISTRATOR": {
        "manage_users", "assign_roles", "configure_integrations", "view_audit_trail",
    },
    "SERVICE_ACCOUNT": {
        "read_telemetry", "write_telemetry",
    },
}


class AuthorizationDecision:
    """Represents a structured result from the permission checker engine.

    BR-051-007: Every authorization decision is explainable.
    """

    def __init__(self, authorized: bool, reason: str, code: str = "DENIED") -> None:
        self.authorized = authorized
        self.reason = reason
        self.code = code  # AUTHORIZED, DENIED, APPROVAL_REQUIRED

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized": self.authorized,
            "reason": self.reason,
            "code": self.code,
        }
