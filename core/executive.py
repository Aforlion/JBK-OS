from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ExecutiveStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"
    SUSPENDED = "SUSPENDED"


class Executive:
    _next_id = 1

    def __init__(
        self,
        title: str,
        mission: str,
        executive_id: str | None = None,
        status: ExecutiveStatus | str = ExecutiveStatus.AVAILABLE,
    ) -> None:
        if not title:
            raise ValueError("Executive title is required.")
        if not mission:
            raise ValueError("Executive mission is required.")

        self._id = executive_id or self._generate_id()
        self.title = title
        self.mission = mission
        self.status = self._normalize_status(status)
        self.assigned_work_orders: list[Any] = []
        self.completed_work_orders: list[Any] = []
        self.created_at = self._current_timestamp()
        self.updated_at = self.created_at

    @property
    def id(self) -> str:
        return self._id

    def receive_work_order(self, work_order: Any, actor: str = "system") -> Any:
        self._require_work_order(work_order)
        if work_order in self.completed_work_orders:
            raise ValueError("Completed work order cannot be reassigned.")
        if work_order not in self.assigned_work_orders:
            self.assigned_work_orders.append(work_order)
            self.updated_at = self._current_timestamp()
            self._log_state_change("receive_work_order", actor, "received")
        return work_order

    def accept_work_order(self, work_order: Any, actor: str = "system") -> Any:
        self._require_assigned_work_order(work_order)
        self.status = ExecutiveStatus.BUSY
        self.updated_at = self._current_timestamp()
        self._log_state_change("accept_work_order", actor, "accepted")
        return work_order

    def complete_work_order(self, work_order: Any, actor: str = "system") -> Any:
        self._require_assigned_work_order(work_order)
        self.assigned_work_orders.remove(work_order)
        self.completed_work_orders.append(work_order)
        self.status = (
            ExecutiveStatus.AVAILABLE
            if not self.assigned_work_orders
            else ExecutiveStatus.BUSY
        )
        self.updated_at = self._current_timestamp()
        self._log_state_change("complete_work_order", actor, "completed")
        return work_order

    def submit_deliverable(
        self,
        work_order: Any,
        deliverable: Any,
        actor: str = "system",
    ) -> dict[str, Any]:
        if work_order not in self.completed_work_orders:
            raise ValueError("Deliverables can only be submitted for completed work orders.")
        if deliverable is None:
            raise ValueError("Deliverable is required.")

        self.updated_at = self._current_timestamp()
        self._log_state_change("submit_deliverable", actor, "submitted")
        return {
            "executive_id": self.id,
            "work_order": self._serialize_value(work_order),
            "deliverable": self._serialize_value(deliverable),
            "submitted_at": self.updated_at,
        }

    def generate_report(self) -> dict[str, Any]:
        return {
            "executive": self.to_dict(),
            "summary": {
                "assigned_work_order_count": len(self.assigned_work_orders),
                "completed_work_order_count": len(self.completed_work_orders),
                "status": self.status.value,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "mission": self.mission,
            "status": self.status.value,
            "assigned_work_orders": [
                self._serialize_value(work_order)
                for work_order in self.assigned_work_orders
            ],
            "completed_work_orders": [
                self._serialize_value(work_order)
                for work_order in self.completed_work_orders
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _generate_id(cls) -> str:
        executive_id = f"EXEC-{cls._next_id:04d}"
        cls._next_id += 1
        return executive_id

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_status(status: ExecutiveStatus | str) -> ExecutiveStatus:
        try:
            return ExecutiveStatus(status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in ExecutiveStatus)
            raise ValueError(f"Invalid executive status. Allowed values: {allowed_statuses}.") from exc

    @staticmethod
    def _require_work_order(work_order: Any) -> None:
        if work_order is None:
            raise ValueError("Work order is required.")

    def _require_assigned_work_order(self, work_order: Any) -> None:
        self._require_work_order(work_order)
        if work_order not in self.assigned_work_orders:
            raise ValueError("Work order is not assigned to this executive.")

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
