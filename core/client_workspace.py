from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class WorkspaceSection:
    """Represents a section in the client portal workspace (e.g. Projects, Deliverables)."""

    def __init__(self, section_id: str, title: str, status: str, items: list[dict[str, Any]] | None = None) -> None:
        self.section_id = section_id
        self.title = title
        self.status = status
        self.items = items or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "status": self.status,
            "items": self.items,
        }


class WorkspaceNotification:
    """Represents a client-visible notification on their workspace."""

    def __init__(self, notification_id: str, title: str, message: str, severity: str, timestamp: str | None = None) -> None:
        self.notification_id = notification_id
        self.title = title
        self.message = message
        self.severity = severity
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


class WorkspaceActivity:
    """Represents an item in the client-facing activity feed."""

    def __init__(self, activity_id: str, title: str, category: str, timestamp: str, details: str = "") -> None:
        self.activity_id = activity_id
        self.title = title
        self.category = category
        self.timestamp = timestamp
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "title": self.title,
            "category": self.category,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class WorkspaceSummary:
    """Brief metrics summary card for the workspace."""

    def __init__(self, active_projects_count: int, pending_approvals_count: int, balance_due: float) -> None:
        self.active_projects_count = active_projects_count
        self.pending_approvals_count = pending_approvals_count
        self.balance_due = balance_due

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_projects_count": self.active_projects_count,
            "pending_approvals_count": self.pending_approvals_count,
            "balance_due": self.balance_due,
        }


class WorkspacePermission:
    """Defines permission rules for the client workspace."""

    def __init__(self, read_only: bool = False, can_approve: bool = True, can_upload: bool = True) -> None:
        self.read_only = read_only
        self.can_approve = can_approve
        self.can_upload = can_upload

    def to_dict(self) -> dict[str, Any]:
        return {
            "read_only": self.read_only,
            "can_approve": self.can_approve,
            "can_upload": self.can_upload,
        }


class ClientWorkspace:
    """Main client portal workspace view model container.

    BR-048-010: Fully serializable to dictionary format.
    """

    def __init__(
        self,
        client_id: str,
        company: str,
        summary: WorkspaceSummary,
        sections: list[WorkspaceSection] | None = None,
        notifications: list[WorkspaceNotification] | None = None,
        activities: list[WorkspaceActivity] | None = None,
        permissions: WorkspacePermission | None = None,
        generated_at: str | None = None,
    ) -> None:
        self.client_id = client_id
        self.company = company
        self.summary = summary
        self.sections = sections or []
        self.notifications = notifications or []
        self.activities = activities or []
        self.permissions = permissions or WorkspacePermission()
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "company": self.company,
            "summary": self.summary.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "notifications": [n.to_dict() for n in self.notifications],
            "activities": [a.to_dict() for a in self.activities],
            "permissions": self.permissions.to_dict(),
            "generated_at": self.generated_at,
        }
