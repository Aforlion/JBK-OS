from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.client_profile import ClientProfile
from core.crm_report import CRMReport
from core.knowledge import KnowledgeItem, KnowledgeStatus
from core.client_success_plan import (
    SupportSchedule,
    RenewalOpportunity,
    UpsellOpportunity,
    RiskAlert,
    ClientSuccessPlan,
)
from core.client_success_report import ClientSuccessReport

LOGGER = logging.getLogger(__name__)

class ClientSuccessEngine:
    """Post-delivery client success evaluation engine. Strictly advisory."""

    def __init__(self) -> None:
        self._report_counter = 1
        self._knowledge_counter = 1

    def evaluate_success(
        self,
        profile: ClientProfile,
        crm_report: CRMReport | None = None,
        project_closure_report: dict[str, Any] | None = None,
        knowledge_registry: Any | None = None,
    ) -> ClientSuccessReport:
        """Evaluate client success lifecycle, opportunities, and risks. Purely advisory (BR-043-005)."""
        if not profile:
            raise ValueError("Client profile is required.")

        # 1. Determine customer success status
        status = self._determine_status(profile)

        # 2. Recommend support schedule
        support_schedule = self._determine_support_schedule(status)

        # 3. Detect renewal opportunities
        renewals = self._detect_renewals(profile)

        # 4. Detect upsell opportunities
        upsells = self._detect_upsells(profile)

        # 5. Measure relationship trend
        trend = self._measure_relationship_trend(profile)

        # 6. Risk detection
        risks = self._detect_risks(profile, crm_report)

        # 7. Generate executive recommendations
        recommendations = self._generate_recommendations(profile, status, trend, renewals, upsells, risks)

        # 8. Knowledge Capture
        if knowledge_registry:
            self._capture_knowledge(profile, status, trend, knowledge_registry)

        report_id = f"CSR-{self._report_counter:04d}"
        self._report_counter += 1

        return ClientSuccessReport(
            report_id=report_id,
            client_id=profile.client_id,
            status=status,
            support_schedule=support_schedule,
            renewal_opportunities=renewals,
            upsell_opportunities=upsells,
            relationship_trend=trend,
            executive_recommendations=recommendations,
            risk_alerts=risks,
        )

    def _determine_status(self, profile: ClientProfile) -> str:
        """Determines success status ONBOARDING, ACTIVE, ADOPTION, STABLE, AT_RISK, ADVOCATE, LOST."""
        if profile.relationship_status == "Critical" and profile.satisfaction_score <= 1.5:
            return "LOST"
        if profile.relationship_status in ("Critical", "At Risk") or profile.satisfaction_score <= 2.5:
            return "AT_RISK"
        if len(profile.active_projects) > 0 and len(profile.past_projects) == 0:
            return "ONBOARDING"
        if len(profile.active_projects) > 0 and len(profile.past_projects) > 0:
            return "ACTIVE"
        if len(profile.past_projects) > 0:
            if profile.satisfaction_score >= 4.5 and profile.trust_score >= 90.0:
                return "ADVOCATE"
            if profile.satisfaction_score >= 3.5:
                return "ADOPTION"
        return "STABLE"

    def _determine_support_schedule(self, status: str) -> SupportSchedule:
        """Recommend support schedule based on success status."""
        today = datetime.now(timezone.utc).date()
        if status in ("ONBOARDING", "AT_RISK"):
            frequency = "Weekly"
            next_date = (today + timedelta(days=7)).isoformat()
        elif status == "ACTIVE":
            frequency = "Monthly"
            next_date = (today + timedelta(days=30)).isoformat()
        elif status in ("ADOPTION", "STABLE"):
            frequency = "Quarterly"
            next_date = (today + timedelta(days=90)).isoformat()
        else:  # ADVOCATE
            frequency = "Annual"
            next_date = (today + timedelta(days=365)).isoformat()

        return SupportSchedule(frequency=frequency, next_date=next_date)

    def _detect_renewals(self, profile: ClientProfile) -> list[RenewalOpportunity]:
        """Detect renewal opportunities (BR-043-003)."""
        renewals = []
        if profile.renewal_date:
            renewals.append(RenewalOpportunity(
                renewal_type="Support contract renewal",
                date=profile.renewal_date,
                estimated_value=profile.lifetime_value * 0.2 if profile.lifetime_value > 0 else 5000.0,
                confidence="High" if profile.trust_score >= 70.0 else "Medium"
            ))
        return renewals

    def _detect_upsells(self, profile: ClientProfile) -> list[UpsellOpportunity]:
        """Detect upsell opportunities (BR-043-004)."""
        upsells = []
        if len(profile.past_projects) > 0:
            upsells.append(UpsellOpportunity(
                upsell_type="AI Automation Upgrade",
                reasoning="Client has successful project history. Adding AI capability expands automation.",
                value=25000.0
            ))
        if profile.organization_size >= 100:
            upsells.append(UpsellOpportunity(
                upsell_type="Analytics Dashboard Implementation",
                reasoning="Large organization size benefits from unified reporting visualizations.",
                value=15000.0
            ))
        if len(profile.active_projects) == 0:
            upsells.append(UpsellOpportunity(
                upsell_type="Standard Maintenance Package",
                reasoning="No active projects. Maintenance contract secures ongoing post-delivery system stability.",
                value=8000.0
            ))
        return upsells

    def _measure_relationship_trend(self, profile: ClientProfile) -> str:
        """Measure relationship trend (Improving, Stable, Declining)."""
        if profile.trust_score >= 80.0 and profile.satisfaction_score >= 4.0:
            return "Improving"
        if profile.trust_score < 50.0 or profile.satisfaction_score < 3.0:
            return "Declining"
        return "Stable"

    def _detect_risks(self, profile: ClientProfile, crm_report: CRMReport | None) -> list[RiskAlert]:
        """Detect risks (no interaction for 90 days, complaints, declining health, etc.)."""
        risks = []
        if profile.relationship_status in ("Critical", "At Risk"):
            risks.append(RiskAlert(
                risk_type="declining health",
                description=f"CRM health is currently categorized as {profile.relationship_status}",
                severity="High"
            ))
        if crm_report and any("complaint" in risk.lower() for risk in crm_report.risks):
            risks.append(RiskAlert(
                risk_type="open complaints",
                description="Client has active, unresolved complaints in CRM records.",
                severity="Medium"
            ))
        return risks

    def _generate_recommendations(
        self,
        profile: ClientProfile,
        status: str,
        trend: str,
        renewals: list[RenewalOpportunity],
        upsells: list[UpsellOpportunity],
        risks: list[RiskAlert],
    ) -> list[str]:
        """Generate executive recommendations with reasoning (advisory only)."""
        recs = []
        if status == "AT_RISK":
            recs.append("Recommend immediate Executive Visit: Direct outreach by JBK CEO is advised because relationship trend is declining.")
        elif status == "ONBOARDING":
            recs.append("Schedule weekly onboarding check-in: Ensure project milestones align with stakeholder expectations.")
        
        if upsells:
            best_upsell = upsells[0]
            recs.append(f"Offer {best_upsell.upsell_type}: Recommended because: {best_upsell.reasoning}")

        if renewals:
            best_renewal = renewals[0]
            recs.append(f"Prepare renewal proposal for date {best_renewal.date}: Proactively secure contract renewal.")

        if not recs:
            recs.append("Schedule quarterly review: Maintain standard client engagement and monitor satisfaction.")

        return recs

    def _capture_knowledge(self, profile: ClientProfile, status: str, trend: str, registry: Any) -> None:
        """Register a KnowledgeItem summarizing success patterns (BR-043-008)."""
        idx = self._knowledge_counter
        self._knowledge_counter += 1
        
        ki = KnowledgeItem(
            knowledge_id=f"KI-S{idx:03d}",
            title=f"Success Strategy: {profile.company}",
            category="Client Success",
            owner="ClientSuccessEngine",
            source="calculated",
            tags=["success", profile.company.lower()],
            description=(
                f"Client success patterns for {profile.company}. Status: {status}, "
                f"Trend: {trend}, Trust Score: {profile.trust_score}."
            ),
            version="1.0",
            status=KnowledgeStatus.ACTIVE
        )
        registry.register(ki)
        LOGGER.info("object_id=%s action=capture_success_knowledge actor=system result=registered", ki.knowledge_id)
