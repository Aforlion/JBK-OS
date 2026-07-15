from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class DeliverableStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class Deliverable:
    _next_id = 1

    def __init__(
        self,
        project_id: str,
        work_order_id: str,
        title: str,
        author: str,
        content: Any = "",
        deliverable_id: str | None = None,
    ) -> None:
        if not project_id:
            raise ValueError("Project ID is required.")
        if not work_order_id:
            raise ValueError("Work order ID is required.")
        if not title:
            raise ValueError("Deliverable title is required.")
        if not author:
            raise ValueError("Deliverable author is required.")

        self._id = deliverable_id or self._generate_id()
        self.project_id = project_id
        self.work_order_id = work_order_id
        self.title = title
        self.author = author
        self.version = 1
        self.status = DeliverableStatus.DRAFT
        self.content = content
        self.created_at = self._current_timestamp()
        self.updated_at = self.created_at

    @property
    def id(self) -> str:
        return self._id

    def update_content(self, content: Any, actor: str = "system") -> Any:
        self.content = content
        self.updated_at = self._current_timestamp()
        self._log_state_change("update_content", actor, "updated")
        return self.content

    def submit_for_review(self, actor: str = "system") -> DeliverableStatus:
        self.status = DeliverableStatus.IN_REVIEW
        self.updated_at = self._current_timestamp()
        self._log_state_change("submit_for_review", actor, "submitted")
        return self.status

    def approve(self, actor: str = "system") -> DeliverableStatus:
        self.status = DeliverableStatus.APPROVED
        self.updated_at = self._current_timestamp()
        self._log_state_change("approve", actor, "approved")
        return self.status

    def reject(self, actor: str = "system") -> DeliverableStatus:
        self.status = DeliverableStatus.REJECTED
        self.updated_at = self._current_timestamp()
        self._log_state_change("reject", actor, "rejected")
        return self.status

    def archive(self, actor: str = "system") -> DeliverableStatus:
        self.status = DeliverableStatus.ARCHIVED
        self.updated_at = self._current_timestamp()
        self._log_state_change("archive", actor, "archived")
        return self.status

    def increment_version(self, actor: str = "system") -> int:
        self.version += 1
        self.updated_at = self._current_timestamp()
        self._log_state_change("increment_version", actor, "incremented")
        return self.version

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "work_order_id": self.work_order_id,
            "title": self.title,
            "author": self.author,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "work_order_id": self.work_order_id,
            "title": self.title,
            "author": self.author,
            "version": self.version,
            "status": self.status.value,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _generate_id(cls) -> str:
        deliverable_id = f"DEL-{cls._next_id:04d}"
        cls._next_id += 1
        return deliverable_id

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log_state_change(self, action: str, actor: str, result: str) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            self.updated_at,
            self.id,
            action,
            actor,
            result,
        )
