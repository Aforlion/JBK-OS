from __future__ import annotations

from typing import Any

from core.financial_snapshot import FinancialSnapshot


class FinancialReport:
    """Financial report output object with executive summary, KPIs, warnings, and recommendations.

    Every recommendation must include explainability (BR-044-010):
        why, calculations, assumptions.
    """

    def __init__(
        self,
        report_id: str,
        executive_summary: str = "",
        kpis: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        recommendations: list[dict[str, str]] | None = None,
        cash_health: str = "Healthy",
        outstanding_invoices: list[dict[str, Any]] | None = None,
        projected_runway_days: float = 0.0,
        snapshot: FinancialSnapshot | None = None,
    ) -> None:
        self.report_id = report_id
        self.executive_summary = executive_summary
        self.kpis = kpis or {}
        self.warnings = warnings or []
        self.recommendations = recommendations or []
        self.cash_health = cash_health
        self.outstanding_invoices = outstanding_invoices or []
        self.projected_runway_days = projected_runway_days
        self.snapshot = snapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "executive_summary": self.executive_summary,
            "kpis": self.kpis,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "cash_health": self.cash_health,
            "outstanding_invoices": self.outstanding_invoices,
            "projected_runway_days": self.projected_runway_days,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
        }
