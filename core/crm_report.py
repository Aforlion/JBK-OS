from __future__ import annotations

from typing import Any

class CRMReport:
    """Represents a generated CRM health and recommendation report for a client."""

    def __init__(
        self,
        report_id: str,
        client_id: str,
        relationship_score: float,
        upcoming_renewals: list[dict[str, Any]] | None = None,
        opportunities: list[str] | None = None,
        risks: list[str] | None = None,
        recommended_actions: list[str] | None = None,
    ) -> None:
        self.report_id = report_id
        self.client_id = client_id
        self.relationship_score = relationship_score
        self.upcoming_renewals = upcoming_renewals or []
        self.opportunities = opportunities or []
        self.risks = risks or []
        self.recommended_actions = recommended_actions or []

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to dictionary."""
        return {
            "report_id": self.report_id,
            "client_id": self.client_id,
            "relationship_score": self.relationship_score,
            "upcoming_renewals": self.upcoming_renewals,
            "opportunities": self.opportunities,
            "risks": self.risks,
            "recommended_actions": self.recommended_actions,
        }
