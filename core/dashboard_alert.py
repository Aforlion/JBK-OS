from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

# Valid alert severities
ALERT_SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")

# Severity weights for sorting (CRITICAL first, BR-046-004)
SEVERITY_WEIGHTS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "INFO": 1,
}


class DashboardAlert:
    """Represents an executive alert.

    BR-046-009: Fully serializable.
    """

    def __init__(
        self,
        alert_id: str,
        severity: str,
        category: str,
        title: str,
        description: str,
        recommended_action: str = "",
        source_engine: str = "",
        created_at: str | None = None,
    ) -> None:
        if severity not in ALERT_SEVERITIES:
            raise ValueError(f"Invalid severity: {severity}. Must be one of {ALERT_SEVERITIES}")

        self.alert_id = alert_id
        self.severity = severity
        self.category = category
        self.title = title
        self.description = description
        self.recommended_action = recommended_action
        self.source_engine = source_engine
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @property
    def severity_weight(self) -> int:
        return SEVERITY_WEIGHTS.get(self.severity, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "recommended_action": self.recommended_action,
            "source_engine": self.source_engine,
            "created_at": self.created_at,
        }
