from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class SystemHealthReport:
    """Consolidated operational health status and telemetry report.

    BR-050-010: Monitoring produces explainable reports carrying recommended corrective actions.
    BR-050-006: Fully serializable to dictionary format.
    """

    def __init__(
        self,
        report_id: str,
        subsystem_health: dict[str, str],
        warnings: list[str] | None = None,
        failures: list[str] | None = None,
        recommendations: list[dict[str, str]] | None = None,
        telemetry_summary: dict[str, Any] | None = None,
        uptime_seconds: int = 0,
        availability_pct: float = 100.0,
        timestamp: str | None = None,
    ) -> None:
        self.report_id = report_id
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.subsystem_health = subsystem_health  # Sourced engines health state
        self.warnings = warnings or []
        self.failures = failures or []
        self.recommendations = recommendations or []  # Explainability metadata
        self.telemetry_summary = telemetry_summary or {}
        self.uptime_seconds = uptime_seconds
        self.availability_pct = availability_pct

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "subsystem_health": self.subsystem_health,
            "warnings": self.warnings,
            "failures": self.failures,
            "recommendations": self.recommendations,
            "telemetry_summary": self.telemetry_summary,
            "uptime_seconds": self.uptime_seconds,
            "availability_pct": self.availability_pct,
        }
