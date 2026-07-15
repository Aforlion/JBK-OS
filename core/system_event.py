from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

# Valid categories and severities
EVENT_CATEGORIES = ("SECURITY", "SYSTEM", "INTEGRATION", "PROCESS")
EVENT_SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")


class SystemEvent:
    """Represents a runtime operational or system event.

    BR-050-003: Every event receives a timestamp.
    BR-050-006: Fully serializable to dictionary format.
    """

    def __init__(
        self,
        event_id: str,
        engine: str,
        category: str,
        severity: str,
        message: str,
        project_id: str | None = None,
        client_id: str | None = None,
        executive_id: str | None = None,
        timestamp: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if category not in EVENT_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {EVENT_CATEGORIES}")
        if severity not in EVENT_SEVERITIES:
            raise ValueError(f"Invalid severity: {severity}. Must be one of {EVENT_SEVERITIES}")

        self.event_id = event_id
        # BR-050-003: Timestamp enforcement
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.engine = engine
        self.category = category
        self.severity = severity
        self.message = message
        self.project_id = project_id
        self.client_id = client_id
        self.executive_id = executive_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "engine": self.engine,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "project_id": self.project_id,
            "client_id": self.client_id,
            "executive_id": self.executive_id,
            "metadata": self.metadata,
        }
