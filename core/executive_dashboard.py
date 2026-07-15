from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.dashboard_section import DashboardSection
from core.dashboard_alert import DashboardAlert
from core.executive_kpi import ExecutiveKPI


class ExecutiveDashboard:
    """Represents the complete executive dashboard.

    BR-046-009: Fully serializable.
    BR-046-010: Render-agnostic. No HTML/Markdown/terminal formatting.
    """

    def __init__(
        self,
        dashboard_id: str,
        company_status: str,
        sections: list[DashboardSection] | None = None,
        alerts: list[DashboardAlert] | None = None,
        kpis: list[ExecutiveKPI] | None = None,
        recommendations: list[dict[str, str]] | None = None,
        executive_summary: str = "",
        generated_at: str | None = None,
    ) -> None:
        self.dashboard_id = dashboard_id
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self.company_status = company_status
        self.sections = sections or []
        self.alerts = alerts or []
        self.kpis = kpis or []
        self.recommendations = recommendations or []
        self.executive_summary = executive_summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "generated_at": self.generated_at,
            "company_status": self.company_status,
            "sections": [s.to_dict() for s in self.sections],
            "alerts": [a.to_dict() for a in self.alerts],
            "kpis": [k.to_dict() for k in self.kpis],
            "recommendations": self.recommendations,
            "executive_summary": self.executive_summary,
        }
