from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class WorkOrderPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkOrderStatus(str, Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkOrder:
    _next_id = 1

    def __init__(
        self,
        project_id: str,
        title: str,
        objective: str,
        work_order_id: str | None = None,
        assigned_by: str | None = None,
        assigned_to: str | None = None,
        priority: WorkOrderPriority | str = WorkOrderPriority.MEDIUM,
    ) -> None:
        if not project_id:
            raise ValueError("Project ID is required.")
        if not title:
            raise ValueError("Work order title is required.")
        if not objective:
            raise ValueError("Work order objective is required.")

        self._id = work_order_id or self._generate_id()
        self.project_id = project_id
        self.title = title
        self.objective = objective
        self.assigned_by = assigned_by
        self.assigned_to = assigned_to
        self.priority = self._normalize_priority(priority)
        self.status = WorkOrderStatus.CREATED
        self.deliverable_id: str | None = None
        self.created_at = self._current_timestamp()
        self.assigned_at: str | None = None
        self.completed_at: str | None = None
        self.updated_at = self.created_at

    @property
    def id(self) -> str:
        return self._id

    def assign(self, assigned_by: str, assigned_to: str, actor: str = "system") -> None:
        if not assigned_by:
            raise ValueError("Assigned by is required.")
        if not assigned_to:
            raise ValueError("Assigned to is required.")

        self.assigned_by = assigned_by
        self.assigned_to = assigned_to
        self.status = WorkOrderStatus.ASSIGNED
        self.assigned_at = self._current_timestamp()
        self.updated_at = self.assigned_at
        self._log_state_change("assign", actor, "assigned")

    def accept(self, actor: str = "system") -> None:
        self._require_assignment()
        self.status = WorkOrderStatus.ACCEPTED
        self.updated_at = self._current_timestamp()
        self._log_state_change("accept", actor, "accepted")

    def start(self, actor: str = "system") -> None:
        self._require_assignment()
        self.status = WorkOrderStatus.IN_PROGRESS
        self.updated_at = self._current_timestamp()
        self._log_state_change("start", actor, "started")

    def complete(self, actor: str = "system") -> None:
        self.status = WorkOrderStatus.COMPLETED
        self.completed_at = self._current_timestamp()
        self.updated_at = self.completed_at
        self._log_state_change("complete", actor, "completed")

    def cancel(self, actor: str = "system") -> None:
        self.status = WorkOrderStatus.CANCELLED
        self.updated_at = self._current_timestamp()
        self._log_state_change("cancel", actor, "cancelled")

    def attach_deliverable(self, deliverable_id: str, actor: str = "system") -> None:
        if not deliverable_id:
            raise ValueError("Deliverable ID is required.")

        self.deliverable_id = deliverable_id
        self.updated_at = self._current_timestamp()
        self._log_state_change("attach_deliverable", actor, "attached")

    def update_priority(
        self,
        priority: WorkOrderPriority | str,
        actor: str = "system",
    ) -> WorkOrderPriority:
        self.priority = self._normalize_priority(priority)
        self.updated_at = self._current_timestamp()
        self._log_state_change("update_priority", actor, "updated")
        return self.priority

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_by": self.assigned_by,
            "assigned_to": self.assigned_to,
            "deliverable_id": self.deliverable_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "objective": self.objective,
            "assigned_by": self.assigned_by,
            "assigned_to": self.assigned_to,
            "priority": self.priority.value,
            "status": self.status.value,
            "deliverable_id": self.deliverable_id,
            "created_at": self.created_at,
            "assigned_at": self.assigned_at,
            "completed_at": self.completed_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _generate_id(cls) -> str:
        work_order_id = f"WO-{cls._next_id:04d}"
        cls._next_id += 1
        return work_order_id

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_priority(priority: WorkOrderPriority | str) -> WorkOrderPriority:
        try:
            return WorkOrderPriority(priority)
        except ValueError as exc:
            allowed_priorities = ", ".join(priority.value for priority in WorkOrderPriority)
            raise ValueError(f"Invalid work order priority. Allowed values: {allowed_priorities}.") from exc

    def _require_assignment(self) -> None:
        if not self.assigned_by or not self.assigned_to:
            raise ValueError("Work order must be assigned first.")

    def _log_state_change(self, action: str, actor: str, result: str) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            self.updated_at,
            self.id,
            action,
            actor,
            result,
        )
