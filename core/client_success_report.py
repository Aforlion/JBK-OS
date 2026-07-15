from __future__ import annotations

from typing import Any
from core.client_success_plan import SupportSchedule, RenewalOpportunity, UpsellOpportunity, RiskAlert

class ClientSuccessReport:
    """Represents a generated evaluation report outlining post-delivery client status."""

    def __init__(
        self,
        report_id: str,
        client_id: str,
        status: str,
        support_schedule: SupportSchedule | None = None,
        renewal_opportunities: list[RenewalOpportunity] | None = None,
        upsell_opportunities: list[UpsellOpportunity] | None = None,
        relationship_trend: str = "Stable",
        executive_recommendations: list[str] | None = None,
        risk_alerts: list[RiskAlert] | None = None,
    ) -> None:
        self.report_id = report_id
        self.client_id = client_id
        self.status = status  # ONBOARDING, ACTIVE, ADOPTION, STABLE, AT_RISK, ADVOCATE, LOST
        self.support_schedule = support_schedule
        self.renewal_opportunities = renewal_opportunities or []
        self.upsell_opportunities = upsell_opportunities or []
        self.relationship_trend = relationship_trend  # Improving, Stable, Declining
        self.executive_recommendations = executive_recommendations or []
        self.risk_alerts = risk_alerts or []

    def to_dict(self) -> dict[str, Any]:
        """Serialize success report to dictionary."""
        return {
            "report_id": self.report_id,
            "client_id": self.client_id,
            "status": self.status,
            "support_schedule": self.support_schedule.to_dict() if self.support_schedule else None,
            "renewal_opportunities": [r.to_dict() for r in self.renewal_opportunities],
            "upsell_opportunities": [u.to_dict() for u in self.upsell_opportunities],
            "relationship_trend": self.relationship_trend,
            "executive_recommendations": self.executive_recommendations,
            "risk_alerts": [r.to_dict() for r in self.risk_alerts],
        }
