from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone
import logging

LOGGER = logging.getLogger(__name__)


class KnowledgeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"
    DRAFT = "DRAFT"


class KnowledgeItem:
    def __init__(
        self,
        knowledge_id: str,
        title: str,
        category: str,
        owner: str,
        source: str,
        tags: list[str],
        description: str,
        version: str,
        status: KnowledgeStatus | str = KnowledgeStatus.DRAFT,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not knowledge_id:
            raise ValueError("Knowledge ID is required.")
        if not title:
            raise ValueError("Knowledge title is required.")
        if not category:
            raise ValueError("Knowledge category is required.")
        if not owner:
            raise ValueError("Knowledge owner is required.")
        if not source:
            raise ValueError("Knowledge source is required.")
        if not version:
            raise ValueError("Knowledge version is required.")
        if status is None:
            raise ValueError("Knowledge status is required.")

        self.knowledge_id = knowledge_id
        self.title = title
        self.category = category
        self.owner = owner
        self.source = source
        self.tags = [t.strip() for t in tags] if tags else []
        self.description = description or ""
        self.version = version
        self.status = (
            status if isinstance(status, KnowledgeStatus) else self._normalize_status(status)
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

    @property
    def id(self) -> str:
        return self.knowledge_id

    def update_status(self, status: KnowledgeStatus | str, actor: str = "system") -> KnowledgeStatus:
        old_status = self.status
        self.status = (
            status if isinstance(status, KnowledgeStatus) else self._normalize_status(status)
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()
        LOGGER.info(
            "object_id=%s action=update_status actor=%s old_status=%s new_status=%s",
            self.id,
            actor,
            old_status.value,
            self.status.value,
        )
        return self.status

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.category.lower()
            or q in self.owner.lower()
            or q in self.source.lower()
            or any(q in tag.lower() for tag in self.tags)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "category": self.category,
            "owner": self.owner,
            "status": self.status.value,
            "version": self.version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "category": self.category,
            "owner": self.owner,
            "source": self.source,
            "tags": list(self.tags),
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def _normalize_status(status: KnowledgeStatus | str) -> KnowledgeStatus:
        try:
            return KnowledgeStatus(status)
        except ValueError as exc:
            allowed_statuses = ", ".join(s.value for s in KnowledgeStatus)
            raise ValueError(
                f"Invalid knowledge status. Allowed values: {allowed_statuses}."
            ) from exc
