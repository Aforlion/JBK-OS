from __future__ import annotations

from typing import Any

from core.executive_meeting import AgendaItem
from core.project_registry import ProjectRegistry
from core.chief_of_staff import ChiefOfStaff
from core.strategic_intelligence_report import StrategicIntelligenceReport


class AgendaGenerator:
    """Helper that dynamically generates structured agenda items (BR-040-004)."""

    def generate(
        self,
        project_registry: ProjectRegistry | None = None,
        strategic_intel: StrategicIntelligenceReport | None = None,
        chief_of_staff: ChiefOfStaff | None = None,
    ) -> list[AgendaItem]:
        agenda: list[AgendaItem] = []

        # 1. Review Active Projects
        if project_registry:
            active_count = len([p for p in project_registry.list_projects() if getattr(p.status, "value", p.status) == "ACTIVE"])
            if active_count > 0:
                agenda.append(
                    AgendaItem(
                        title="Active Projects Status Review",
                        owner="COO",
                        priority="HIGH",
                        discussion=f"Verify progress on {active_count} active projects and check for delivery bottlenecks.",
                    )
                )

        # 2. Strategic Intelligence Opportunities
        if strategic_intel:
            opps = len(getattr(strategic_intel, "emerging_opportunities", []))
            if opps > 0:
                agenda.append(
                    AgendaItem(
                        title="Emerging Market Opportunities Analysis",
                        owner="CMO",
                        priority="MEDIUM",
                        discussion=f"Review {opps} high-confidence strategic opportunities identified on market radar.",
                    )
                )

        # 3. CEO Approvals & Escalations
        if chief_of_staff:
            brief = chief_of_staff.generate_executive_brief()
            ceo_attention = len(brief.get("items_requiring_ceo_attention", []))
            if ceo_attention > 0:
                agenda.append(
                    AgendaItem(
                        title="CEO Approvals & Critical Escalations",
                        owner="CEO",
                        priority="CRITICAL",
                        discussion=f"Review and resolve {ceo_attention} critical bottlenecks or pending approvals.",
                    )
                )

        # Fallback default agenda
        if not agenda:
            agenda.append(
                AgendaItem(
                    title="Company Health & Operations Overview",
                    owner="Chief of Staff",
                    priority="MEDIUM",
                    discussion="General alignment on operational efficiency.",
                )
            )

        return agenda
