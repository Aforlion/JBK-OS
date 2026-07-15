from __future__ import annotations

from typing import Any

class ClientProfile:
    """Represents a permanent customer profile in JBK OS CRM."""

    def __init__(
        self,
        client_id: str,
        company: str,
        contact_people: list[str] | None = None,
        industry: str = "General",
        organization_size: int = 1,
        risk_rating: str = "Medium",
        lifetime_value: float = 0.0,
        satisfaction_score: float = 5.0,
        relationship_status: str = "Active",
        active_projects: list[str] | None = None,
        past_projects: list[str] | None = None,
        support_level: str = "Standard",
        renewal_date: str | None = None,
        trust_score: float = 70.0,
    ) -> None:
        self.client_id = client_id
        self.company = company
        self.contact_people = contact_people or []
        self.industry = industry
        self.organization_size = organization_size
        self.risk_rating = risk_rating
        self.lifetime_value = lifetime_value
        self.satisfaction_score = satisfaction_score
        self.relationship_status = relationship_status
        self.active_projects = active_projects or []
        self.past_projects = past_projects or []
        self.support_level = support_level
        self.renewal_date = renewal_date
        self.trust_score = trust_score

    def to_dict(self) -> dict[str, Any]:
        """Serialize profile to dictionary."""
        return {
            "client_id": self.client_id,
            "company": self.company,
            "contact_people": self.contact_people,
            "industry": self.industry,
            "organization_size": self.organization_size,
            "risk_rating": self.risk_rating,
            "lifetime_value": self.lifetime_value,
            "satisfaction_score": self.satisfaction_score,
            "relationship_status": self.relationship_status,
            "active_projects": self.active_projects,
            "past_projects": self.past_projects,
            "support_level": self.support_level,
            "renewal_date": self.renewal_date,
            "trust_score": self.trust_score,
        }
