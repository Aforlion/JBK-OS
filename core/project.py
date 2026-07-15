from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ProjectStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Project:
    _next_id = 1

    def __init__(
        self,
        title: str,
        client: str,
        description: str,
        project_id: str | None = None,
        status: ProjectStatus | str = ProjectStatus.PLANNED,
    ) -> None:
        if not title:
            raise ValueError("Project title is required.")
        if not client:
            raise ValueError("Project client is required.")
        if not description:
            raise ValueError("Project description is required.")

        self._id = project_id or self._generate_id()
        self.title = title
        self.client = client
        self.description = description
        self.status = self._normalize_status(status)
        self.work_orders: list[Any] = []
        self.deliverables: list[Any] = []
        self.decisions: list[Any] = []
        self.created_at = self._current_timestamp()
        self.updated_at = self.created_at

    @property
    def id(self) -> str:
        return self._id

    def add_work_order(self, work_order: Any, actor: str = "system") -> Any:
        if work_order is None:
            raise ValueError("Work order is required.")
        self.work_orders.append(work_order)
        self.updated_at = self._current_timestamp()
        self._log_state_change("add_work_order", actor, "added")
        return work_order

    def add_deliverable(self, deliverable: Any, actor: str = "system") -> Any:
        if deliverable is None:
            raise ValueError("Deliverable is required.")
        self.deliverables.append(deliverable)
        self.updated_at = self._current_timestamp()
        self._log_state_change("add_deliverable", actor, "added")
        return deliverable

    def record_decision(self, decision: Any, actor: str = "system") -> Any:
        if decision is None:
            raise ValueError("Decision is required.")
        self.decisions.append(decision)
        self.updated_at = self._current_timestamp()
        self._log_state_change("record_decision", actor, "recorded")
        return decision

    def update_status(
        self,
        status: ProjectStatus | str,
        actor: str = "system",
    ) -> ProjectStatus:
        self.status = self._normalize_status(status)
        self.updated_at = self._current_timestamp()
        self._log_state_change("update_status", actor, "updated")
        return self.status

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "client": self.client,
            "status": self.status.value,
            "work_order_count": len(self.work_orders),
            "deliverable_count": len(self.deliverables),
            "decision_count": len(self.decisions),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "client": self.client,
            "description": self.description,
            "status": self.status.value,
            "work_orders": [
                self._serialize_value(work_order)
                for work_order in self.work_orders
            ],
            "deliverables": [
                self._serialize_value(deliverable)
                for deliverable in self.deliverables
            ],
            "decisions": [
                self._serialize_value(decision)
                for decision in self.decisions
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _generate_id(cls) -> str:
        project_id = f"PROJ-{cls._next_id:04d}"
        cls._next_id += 1
        return project_id

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_status(status: ProjectStatus | str) -> ProjectStatus:
        try:
            return ProjectStatus(status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in ProjectStatus)
            raise ValueError(f"Invalid project status. Allowed values: {allowed_statuses}.") from exc

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return value.to_dict()
        if isinstance(value, dict):
            return dict(value)
        if hasattr(value, "__dict__"):
            return dict(value.__dict__)
        return value

    def _log_state_change(self, action: str, actor: str, result: str) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            self.updated_at,
            self.id,
            action,
            actor,
            result,
        )
