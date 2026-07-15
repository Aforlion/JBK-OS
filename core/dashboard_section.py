from __future__ import annotations

from typing import Any

# Valid section statuses
SECTION_STATUSES = ("HEALTHY", "WARNING", "CRITICAL", "UNAVAILABLE")


class DashboardSection:
    """Represents an individual dashboard card.

    BR-046-003: Every dashboard section references its source engine.
    BR-046-006: Unavailable sections display "Unavailable".
    BR-046-009: Fully serializable.
    """

    def __init__(
        self,
        title: str,
        source_engine: str,
        status: str = "HEALTHY",
        priority: int = 3,
        summary: str = "",
        metrics: dict[str, Any] | None = None,
        drill_down_reference: str = "",
    ) -> None:
        if status not in SECTION_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SECTION_STATUSES}")
        if not source_engine or not source_engine.strip():
            raise ValueError("Source engine is required (BR-046-003).")

        self.title = title
        self.source_engine = source_engine
        self.status = status
        self.priority = priority
        self.summary = summary
        self.metrics = metrics or {}
        self.drill_down_reference = drill_down_reference

        # BR-046-006: Unavailable sections display: "Unavailable"
        if status == "UNAVAILABLE":
            self.summary = "Unavailable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "source_engine": self.source_engine,
            "status": self.status,
            "priority": self.priority,
            "summary": self.summary,
            "metrics": self.metrics,
            "drill_down_reference": self.drill_down_reference,
        }
