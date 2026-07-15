from __future__ import annotations

from typing import Any

# Valid trends (BR-046-008)
KPI_TRENDS = ("UP", "DOWN", "STABLE", "UNKNOWN")

# Valid KPI statuses
KPI_STATUSES = ("ON_TRACK", "AT_RISK", "CRITICAL")


class ExecutiveKPI:
    """Standard KPI object.

    BR-046-008: Supports trend values: UP, DOWN, STABLE, UNKNOWN.
    BR-046-009: Fully serializable.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        target: Any = None,
        trend: str = "UNKNOWN",
        status: str = "ON_TRACK",
    ) -> None:
        if trend not in KPI_TRENDS:
            raise ValueError(f"Invalid trend: {trend}. Must be one of {KPI_TRENDS}")
        if status not in KPI_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {KPI_STATUSES}")

        self.name = name
        self.value = value
        self.target = target
        self.trend = trend
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "target": self.target,
            "trend": self.trend,
            "status": self.status,
        }
