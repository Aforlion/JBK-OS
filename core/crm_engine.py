from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.client_profile import ClientProfile
from core.client_interaction import ClientInteraction
from core.relationship_health import RelationshipHealth
from core.crm_report import CRMReport

LOGGER = logging.getLogger(__name__)

class CRMEngine:
    """Manages customer profiles, interaction logging, health metrics, and growth recommendations."""

    def __init__(self) -> None:
        self._profiles: dict[str, ClientProfile] = {}
        self._interactions: list[ClientInteraction] = []
        self._client_counter = 1
        self._interaction_counter = 1
        self._report_counter = 1

    def register_client(
        self,
        company: str,
        industry: str = "General",
        organization_size: int = 1,
        contact_people: list[str] | None = None,
        support_level: str = "Standard",
        renewal_date: str | None = None,
    ) -> ClientProfile:
        """Register a new client profile. Enforces duplicate prevention per organization (BR-042-001)."""
        if not company or not company.strip():
            raise ValueError("Company name is required.")

        # Check duplicates
        company_clean = company.strip().lower()
        for p in self._profiles.values():
            if p.company.strip().lower() == company_clean:
                raise ValueError(f"Client Profile already exists for organization: {company}")

        client_id = f"CLT-{self._client_counter:04d}"
        self._client_counter += 1

        profile = ClientProfile(
            client_id=client_id,
            company=company.strip(),
            industry=industry,
            organization_size=organization_size,
            contact_people=contact_people,
            support_level=support_level,
            renewal_date=renewal_date,
        )
        self._profiles[client_id] = profile
        self.update_health(client_id)
        LOGGER.info("object_id=%s action=register_client actor=system result=registered", client_id)
        return profile

    def log_interaction(
        self,
        client_id: str,
        interaction_type: str,
        description: str,
        outcome: str = "",
        created_by: str = "system",
        timestamp: str | None = None,
    ) -> ClientInteraction:
        """Log a client interaction (BR-042-003). Recalculates relationship health automatically."""
        if client_id not in self._profiles:
            raise ValueError(f"Client profile not found: {client_id}")

        interaction_id = f"INT-{self._interaction_counter:04d}"
        self._interaction_counter += 1

        interaction = ClientInteraction(
            interaction_id=interaction_id,
            client_id=client_id,
            interaction_type=interaction_type,
            description=description,
            created_by=created_by,
            outcome=outcome,
            timestamp=timestamp,
        )
        self._interactions.append(interaction)
        
        # Satisfaction adjustment if interaction is a complaint
        profile = self._profiles[client_id]
        if interaction_type.strip().lower() == "complaint":
            profile.satisfaction_score = max(1.0, profile.satisfaction_score - 1.0)
        elif interaction_type.strip().lower() == "review meeting":
            profile.satisfaction_score = min(5.0, profile.satisfaction_score + 0.5)

        self.update_health(client_id)
        LOGGER.info("object_id=%s action=log_interaction actor=%s result=logged", interaction_id, created_by)
        return interaction

    def process_project_completion(self, client_id: str, project_id: str, success: bool) -> None:
        """Process project end to update trust score and track active/past projects."""
        if client_id not in self._profiles:
            raise ValueError(f"Client profile not found: {client_id}")

        profile = self._profiles[client_id]
        
        # Link project (BR-042-002)
        if project_id in profile.active_projects:
            profile.active_projects.remove(project_id)
        
        if project_id not in profile.past_projects:
            profile.past_projects.append(project_id)

        # Trust score adjustments
        if success:
            profile.trust_score = min(100.0, profile.trust_score + 5.0)  # BR-042-007
        else:
            profile.trust_score = max(0.0, profile.trust_score - 15.0)   # BR-042-008

        self.update_health(client_id)

    def update_health(self, client_id: str) -> RelationshipHealth:
        """Calculate and update client relationship health status (BR-042-004)."""
        if client_id not in self._profiles:
            raise ValueError(f"Client profile not found: {client_id}")

        profile = self._profiles[client_id]
        client_interactions = [i for i in self._interactions if i.client_id == client_id]
        
        # Count failed projects via trust score depletion rate or track failed count. 
        # For simplicity in calculations, count complaints and support history
        open_complaints = len([i for i in client_interactions if i.interaction_type == "complaint" and ("resolved" not in i.outcome.lower() or "unresolved" in i.outcome.lower())])
        failed_count = len([i for i in client_interactions if "failure" in i.description.lower() or "failed" in i.outcome.lower()])
        
        # Support history factor (BR-042-006)
        support_count = len([i for i in client_interactions if i.interaction_type == "support"])
        if support_count > 5:
            # High support overhead decreases satisfaction slightly if unresolved
            unresolved_support = len([i for i in client_interactions if i.interaction_type == "support" and ("resolved" not in i.outcome.lower() or "unresolved" in i.outcome.lower())])
            if unresolved_support > 2:
                profile.satisfaction_score = max(1.0, profile.satisfaction_score - 0.5)

        health = RelationshipHealth.calculate(
            trust_score=profile.trust_score,
            satisfaction_score=profile.satisfaction_score,
            failed_projects_count=failed_count,
            open_complaints=open_complaints,
        )

        profile.relationship_status = health.health_status
        return health

    def generate_report(self, client_id: str) -> CRMReport:
        """Generate a CRMReport containing health summary, upcoming renewals, and opportunities."""
        if client_id not in self._profiles:
            raise ValueError(f"Client profile not found: {client_id}")

        profile = self._profiles[client_id]
        
        # Calculate relationship score
        # Relationship score = trust_score * 0.6 + (satisfaction_score * 20.0) * 0.4
        relationship_score = (profile.trust_score * 0.6) + ((profile.satisfaction_score * 20.0) * 0.4)
        
        # Renewals predicted (BR-042-009)
        upcoming_renewals = []
        if profile.renewal_date:
            upcoming_renewals.append({
                "renewal_date": profile.renewal_date,
                "probability": "High" if relationship_score >= 70.0 else "Medium" if relationship_score >= 50.0 else "Low"
            })

        opportunities: list[str] = []
        risks: list[str] = []
        recommended_actions: list[str] = []

        # Opportunities
        if profile.satisfaction_score >= 4.0:
            opportunities.append("Case Study: High satisfaction client is a prime candidate for a success story.")
            if profile.organization_size >= 200:
                opportunities.append("Upsell: Enterprise support level package upgrade.")
            else:
                opportunities.append("Cross sell: Implement workflow training package.")
        
        # Risks
        if profile.relationship_status in ("Critical", "At Risk"):
            risks.append(f"Client is at risk! Health status is: {profile.relationship_status}")
        
        # Detect cold client
        is_cold = self._is_client_cold(client_id)
        if is_cold:
            risks.append("Client going cold: No interactions registered in the last 30 days.")
            recommended_actions.append("Quarterly Review: Schedule check-in meeting to re-engage.")

        # General recommendations (BR-042-005)
        if profile.relationship_status == "Critical":
            recommended_actions.append("Executive Visit: Immediate CEO / Director outreach requested.")
        elif profile.satisfaction_score < 3.0:
            recommended_actions.append("Client sync: Schedule remediation call to review pain points.")
        else:
            recommended_actions.append("Routine outreach: Maintain standard touchpoints.")

        # CEO Alerts (BR-042-010)
        is_strategic = self.is_strategic_account(client_id)
        if is_strategic:
            LOGGER.warning("ALERT: CEO visibility required for strategic client %s (%s)", client_id, profile.company)

        report_id = f"REP-{self._report_counter:04d}"
        self._report_counter += 1

        return CRMReport(
            report_id=report_id,
            client_id=client_id,
            relationship_score=round(relationship_score, 1),
            upcoming_renewals=upcoming_renewals,
            opportunities=opportunities,
            risks=risks,
            recommended_actions=recommended_actions,
        )

    def is_strategic_account(self, client_id: str) -> bool:
        """Determines if a client is strategic (LTV >= 100k or size >= 500)."""
        profile = self._profiles[client_id]
        return profile.lifetime_value >= 100000.0 or profile.organization_size >= 500

    def _is_client_cold(self, client_id: str) -> bool:
        """Helper to check if client has had no interactions in 30 days."""
        client_interactions = [i for i in self._interactions if i.client_id == client_id]
        if not client_interactions:
            return True
        
        # Find latest interaction
        latest_str = max(i.timestamp for i in client_interactions)
        try:
            latest = datetime.fromisoformat(latest_str)
            now = datetime.now(timezone.utc)
            if now - latest > timedelta(days=30):
                return True
        except Exception:
            pass
        return False

    def list_clients(self) -> list[ClientProfile]:
        return list(self._profiles.values())

    def get_client(self, client_id: str) -> ClientProfile | None:
        return self._profiles.get(client_id)
