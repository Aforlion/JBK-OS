from __future__ import annotations

import logging
import re
from typing import Any

from core.solution_blueprint import SolutionBlueprint
from core.project_estimate import ProjectEstimate
from core.commercial_proposal import CommercialProposal
from core.discovery_plan import DiscoveryPlan
from core.business_transformation_plan import (
    KPI,
    TransformationObjective,
    ChangeImpact,
    AdoptionPhase,
    BusinessTransformationPlan,
)

LOGGER = logging.getLogger(__name__)

# Fallback adoption phases when no estimate milestones are available
_DEFAULT_ADOPTION_PHASES = [
    {
        "name": "Pilot",
        "description": "Deploy solution to a controlled pilot group and collect feedback.",
        "duration_weeks": 4.0,
        "scope": "Pilot group — limited rollout",
        "key_activities": ["Deploy to pilot users", "Collect feedback", "Resolve critical issues"],
        "success_gate": "Pilot group sign-off and zero critical blockers",
    },
    {
        "name": "Rollout",
        "description": "Expand solution to all affected departments with training and support.",
        "duration_weeks": 6.0,
        "scope": "All affected departments",
        "key_activities": ["Department-by-department rollout", "Training delivery", "Helpdesk activation"],
        "success_gate": "All departments live with adoption rate ≥ 80%",
    },
    {
        "name": "Full Adoption",
        "description": "Achieve full organizational adoption with continuous improvement loops.",
        "duration_weeks": 4.0,
        "scope": "Entire organization",
        "key_activities": ["Monitor KPIs", "Retire legacy processes", "Begin continuous improvement cycle"],
        "success_gate": "All KPI targets met and legacy systems decommissioned",
    },
]


class BusinessTransformationEngine:
    """Stateless engine that converts an approved SolutionBlueprint into a
    BusinessTransformationPlan — a measurable, department-level business change roadmap.

    The engine is purely advisory. It never modifies any input object.
    """

    def __init__(self) -> None:
        self._plan_counter = 1
        self._obj_counter = 1
        self._kpi_counter = 1
        self._impact_counter = 1
        self._phase_counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transform(
        self,
        blueprint: SolutionBlueprint,
        estimate: ProjectEstimate | None = None,
        proposal: CommercialProposal | None = None,
        discovery_plan: DiscoveryPlan | None = None,
        organizational_knowledge: Any | None = None,
    ) -> BusinessTransformationPlan:
        """Produce a BusinessTransformationPlan from an approved solution blueprint."""
        if blueprint is None:
            raise ValueError("SolutionBlueprint is required.")

        plan_id = self._next_plan_id()
        LOGGER.info(
            "object_id=%s action=transform actor=system status=DRAFT blueprint_id=%s",
            plan_id,
            blueprint.blueprint_id,
        )

        warnings: list[str] = []

        # Resolve client from available inputs
        client = (
            getattr(blueprint, "client_summary", "")
            or getattr(estimate, "client_summary", "")
            or "Client"
        )

        # ---- Current State -----------------------------------------------
        current_state = self._build_current_state(blueprint, discovery_plan)

        # ---- Future State -------------------------------------------------
        future_state = self._build_future_state(blueprint)

        # ---- Transformation Objectives -----------------------------------
        objectives = self._build_objectives(blueprint)

        # ---- KPI Dashboard -----------------------------------------------
        kpis = self._build_kpis(blueprint, estimate)

        # ---- Department Impact Analysis ----------------------------------
        impacts = self._build_department_impacts(blueprint)

        # ---- Process Changes ---------------------------------------------
        process_changes = self._build_process_changes(blueprint, discovery_plan)

        # ---- Change Management Plan --------------------------------------
        change_mgmt = self._build_change_management_plan(blueprint, estimate)

        # ---- Training Plan -----------------------------------------------
        training_plan = self._build_training_plan(blueprint)

        # ---- Adoption Strategy -------------------------------------------
        adoption_phases = self._build_adoption_strategy(estimate)

        # ---- Risk Register -----------------------------------------------
        risk_register = self._build_risk_register(blueprint, proposal)

        # ---- Executive Recommendations -----------------------------------
        exec_recs = self._build_executive_recommendations(
            blueprint, proposal, organizational_knowledge
        )

        # ---- Warnings on missing optional inputs -------------------------
        if estimate is None:
            warnings.append(
                "No ProjectEstimate provided; adoption phases use generic 3-phase fallback "
                "and change management plan uses defaults."
            )
        if proposal is None:
            warnings.append(
                "No CommercialProposal provided; commercial risks not included in risk register."
            )
        if discovery_plan is None:
            warnings.append(
                "No DiscoveryPlan provided; current state derived from blueprint only."
            )
        if organizational_knowledge is None:
            warnings.append(
                "No OrganizationalKnowledge provided; historical enrichment unavailable."
            )

        LOGGER.info(
            "object_id=%s action=transform actor=system status=READY blueprint_id=%s "
            "objectives=%d kpis=%d departments=%d phases=%d risks=%d",
            plan_id,
            blueprint.blueprint_id,
            len(objectives),
            len(kpis),
            len(impacts),
            len(adoption_phases),
            len(risk_register),
        )

        return BusinessTransformationPlan(
            plan_id=plan_id,
            blueprint_id=blueprint.blueprint_id,
            client=client,
            current_state_assessment=current_state,
            future_state_vision=future_state,
            transformation_objectives=objectives,
            department_impact_analysis=impacts,
            process_changes=process_changes,
            change_management_plan=change_mgmt,
            training_plan=training_plan,
            adoption_strategy=adoption_phases,
            kpi_dashboard=kpis,
            success_metrics=list(blueprint.success_metrics),
            risk_register=risk_register,
            executive_recommendations=exec_recs,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private builders
    # ------------------------------------------------------------------

    def _build_current_state(
        self,
        blueprint: SolutionBlueprint,
        discovery_plan: DiscoveryPlan | None,
    ) -> dict[str, Any]:
        known_info: list[str] = []
        gaps: list[str] = []
        if discovery_plan is not None:
            known_info = list(discovery_plan.information_already_known)
            gaps = list(discovery_plan.information_still_required)

        return {
            "business_problem": blueprint.business_problem,
            "root_cause_analysis": dict(blueprint.root_cause_analysis),
            "known_information": known_info,
            "information_gaps": gaps,
            "pain_points": list(blueprint.risks),
            "current_limitations": list(blueprint.assumptions),
        }

    def _build_future_state(self, blueprint: SolutionBlueprint) -> dict[str, Any]:
        return {
            "vision_statement": blueprint.executive_recommendation,
            "recommended_solution": dict(blueprint.recommended_solution),
            "business_benefits": list(blueprint.business_benefits),
            "business_objectives": list(blueprint.business_objectives),
            "success_horizon": "Post-implementation steady state",
        }

    def _build_objectives(self, blueprint: SolutionBlueprint) -> list[TransformationObjective]:
        objectives: list[TransformationObjective] = []
        for goal in blueprint.business_objectives:
            obj = TransformationObjective(
                objective_id=self._next_obj_id(),
                title=f"Achieve: {goal}",
                description=(
                    f"Transform business operations to deliver on the goal: '{goal}'. "
                    f"This objective drives the overall transformation towards "
                    f"{blueprint.recommended_solution.get('title', 'the recommended solution')}."
                ),
                linked_business_goals=[goal],
                owner_department=(
                    blueprint.required_departments[0]
                    if blueprint.required_departments
                    else "Leadership"
                ),
                success_criteria=[
                    f"Measurable improvement in: {goal}",
                    "Executive sign-off on objective delivery",
                    "KPI targets met post-implementation",
                ],
                priority="HIGH" if blueprint.estimated_complexity == "High" else "MEDIUM",
            )
            objectives.append(obj)
        return objectives

    def _build_kpis(
        self,
        blueprint: SolutionBlueprint,
        estimate: ProjectEstimate | None,
    ) -> list[KPI]:
        kpis: list[KPI] = []
        departments = blueprint.required_departments or ["Operations"]

        for i, metric in enumerate(blueprint.success_metrics):
            target_value, unit = self._parse_metric(metric)
            dept = departments[i % len(departments)]
            kpi = KPI(
                kpi_id=self._next_kpi_id(),
                name=metric[:80],
                description=f"Business KPI derived from success metric: {metric}",
                baseline="To be established pre-implementation",
                target_value=target_value,
                unit=unit,
                measurement_method=self._infer_measurement_method(metric),
                timeframe=f"Within {estimate.estimated_duration}" if estimate else "Post go-live",
                owner_department=dept,
                source_metric=metric,
            )
            kpis.append(kpi)

        # If no success metrics, produce a single default KPI
        if not kpis:
            kpis.append(KPI(
                kpi_id=self._next_kpi_id(),
                name="Overall Business Outcome Achievement",
                description="Composite measure of transformation success.",
                baseline="Pre-implementation baseline",
                target_value="100",
                unit="%",
                measurement_method="Executive assessment against defined objectives",
                timeframe="6 months post go-live",
                owner_department=departments[0],
                source_metric="",
            ))
        return kpis

    def _build_department_impacts(self, blueprint: SolutionBlueprint) -> list[ChangeImpact]:
        impacts: list[ChangeImpact] = []
        departments = blueprint.required_departments or []

        for dept in departments:
            impact = ChangeImpact(
                impact_id=self._next_impact_id(),
                department=dept,
                impact_level="HIGH" if blueprint.estimated_complexity == "High" else "MEDIUM",
                affected_processes=list(blueprint.technical_considerations[:3]),
                headcount_affected=0,  # unknown without org chart data
                change_description=(
                    f"The {dept} department will adopt "
                    f"{blueprint.recommended_solution.get('title', 'the new solution')}. "
                    f"Existing workflows will be updated to align with new capabilities."
                ),
                training_required=list(blueprint.required_skills[:5]),
                readiness_actions=[
                    f"Brief {dept} leadership on transformation scope",
                    f"Identify {dept} change champions",
                    "Schedule readiness assessment",
                ],
            )
            impacts.append(impact)

        return impacts

    def _build_process_changes(
        self,
        blueprint: SolutionBlueprint,
        discovery_plan: DiscoveryPlan | None,
    ) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []

        for consideration in blueprint.technical_considerations:
            changes.append({
                "process": consideration,
                "change_type": "MODIFY",
                "rationale": f"Technical consideration from solution blueprint.",
                "impacted_departments": list(blueprint.required_departments[:2]),
            })

        if discovery_plan:
            for category in discovery_plan.conversation_categories:
                changes.append({
                    "process": f"{category} workflow",
                    "change_type": "REVIEW",
                    "rationale": "Discovery conversation identified this as an area requiring review.",
                    "impacted_departments": list(blueprint.required_departments[:1]),
                })

        return changes

    def _build_change_management_plan(
        self,
        blueprint: SolutionBlueprint,
        estimate: ProjectEstimate | None,
    ) -> dict[str, Any]:
        strategy = estimate.delivery_strategy if estimate else "Agile"
        assumptions = estimate.key_assumptions if estimate else list(blueprint.assumptions)
        constraints = estimate.known_constraints if estimate else list(blueprint.dependencies)

        return {
            "strategy": strategy,
            "approach": (
                f"Adopt a {strategy} change management approach aligned with the "
                f"solution delivery. Stakeholder engagement, communication planning, "
                f"and resistance management are central to this plan."
            ),
            "key_assumptions": assumptions,
            "known_constraints": constraints,
            "communication_plan": {
                "frequency": "Weekly",
                "channels": ["Executive briefings", "Department newsletters", "Town halls"],
                "key_messages": [
                    f"Why: {blueprint.business_problem[:120]}",
                    f"What: {blueprint.recommended_solution.get('title', 'New solution')}",
                    "How: Phased adoption with training and support",
                ],
            },
            "stakeholder_management": {
                "sponsors": blueprint.required_departments[:1],
                "champions": blueprint.required_departments,
                "resistance_mitigation": (
                    "Proactive communication, early wins, and visible executive sponsorship."
                ),
            },
        }

    def _build_training_plan(self, blueprint: SolutionBlueprint) -> dict[str, Any]:
        return {
            "required_skills": list(blueprint.required_skills),
            "required_capabilities": list(blueprint.required_capabilities),
            "delivery_approach": "Blended learning — online modules, hands-on workshops, and peer coaching",
            "training_schedule": "Commence 4 weeks before go-live; refresher sessions at 30, 60, and 90 days post-launch",
            "target_audiences": list(blueprint.required_departments),
            "success_criterion": "≥ 90% of staff assessed as competent before go-live",
        }

    def _build_adoption_strategy(
        self, estimate: ProjectEstimate | None
    ) -> list[AdoptionPhase]:
        if estimate and estimate.major_milestones:
            phases: list[AdoptionPhase] = []
            for i, milestone in enumerate(estimate.major_milestones):
                phase = AdoptionPhase(
                    phase_id=self._next_phase_id(),
                    name=milestone,
                    description=(
                        f"Adoption phase aligned to delivery milestone: {milestone}."
                    ),
                    sequence=i + 1,
                    duration_weeks=max(2.0, estimate.expected_duration / max(len(estimate.major_milestones), 1)),
                    scope=f"Milestone: {milestone}",
                    key_activities=[
                        f"Deliver milestone: {milestone}",
                        "Stakeholder review and acceptance",
                        "User readiness confirmation",
                    ],
                    success_gate=f"Milestone '{milestone}' accepted by client",
                    responsible_parties=list(estimate.required_departments[:2]),
                )
                phases.append(phase)
            return phases

        # Fallback: generic 3-phase rollout
        phases = []
        for i, phase_def in enumerate(_DEFAULT_ADOPTION_PHASES):
            phases.append(AdoptionPhase(
                phase_id=self._next_phase_id(),
                name=phase_def["name"],
                description=phase_def["description"],
                sequence=i + 1,
                duration_weeks=phase_def["duration_weeks"],
                scope=phase_def["scope"],
                key_activities=list(phase_def["key_activities"]),
                success_gate=phase_def["success_gate"],
                responsible_parties=["Leadership", "Operations"],
            ))
        return phases

    def _build_risk_register(
        self,
        blueprint: SolutionBlueprint,
        proposal: CommercialProposal | None,
    ) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        for risk in blueprint.risks:
            risks.append({
                "risk": risk,
                "source": "Solution Blueprint",
                "severity": "MEDIUM",
                "mitigation": (
                    f"Proactively monitor and manage: {risk}. "
                    "Assign risk owner and review at each adoption gate."
                ),
            })

        if proposal:
            for commercial_risk in proposal.commercial_risks:
                risk_title = commercial_risk.get("risk", str(commercial_risk))
                risks.append({
                    "risk": risk_title,
                    "source": "Commercial Proposal",
                    "severity": commercial_risk.get("severity", "MEDIUM"),
                    "mitigation": commercial_risk.get(
                        "mitigation",
                        f"Review commercial risk '{risk_title}' with legal and finance before contract signing.",
                    ),
                })

        return risks

    def _build_executive_recommendations(
        self,
        blueprint: SolutionBlueprint,
        proposal: CommercialProposal | None,
        organizational_knowledge: Any | None,
    ) -> list[str]:
        recs: list[str] = []

        if blueprint.executive_recommendation:
            recs.append(f"Blueprint: {blueprint.executive_recommendation}")

        if proposal and proposal.executive_recommendation:
            recs.append(f"Commercial: {proposal.executive_recommendation}")

        if organizational_knowledge:
            # Surface top future recommendations from historical knowledge
            for rec in getattr(organizational_knowledge, "future_recommendations", [])[:3]:
                if rec.strip():
                    recs.append(f"Historical insight: {rec}")

        recs.append(
            "Ensure executive sponsorship is visible and active throughout all adoption phases."
        )
        recs.append(
            "Measure and communicate early wins to build momentum and reduce resistance."
        )

        return recs

    # ------------------------------------------------------------------
    # Metric parsing utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_metric(metric: str) -> tuple[str, str]:
        """Extract a numeric target value and unit from a success metric string.

        Returns (target_value_str, unit_str). Falls back to (metric[:40], 'measure').
        """
        # Pattern: number followed by optional % or word unit
        match = re.search(r"(\d+(?:\.\d+)?)\s*(%|[a-zA-Z]+)?", metric)
        if match:
            value = match.group(1)
            unit = (match.group(2) or "").strip() or "measure"
            return value, unit
        return metric[:40], "measure"

    @staticmethod
    def _infer_measurement_method(metric: str) -> str:
        """Infer a measurement method from the metric text."""
        metric_lower = metric.lower()
        if "uptime" in metric_lower or "availability" in metric_lower:
            return "System monitoring dashboards (SLA reports)"
        if "time" in metric_lower or "duration" in metric_lower or "hour" in metric_lower:
            return "Process timing logs and workflow analytics"
        if "cost" in metric_lower or "saving" in metric_lower or "revenue" in metric_lower:
            return "Financial reporting and budget tracking"
        if "%" in metric or "rate" in metric_lower or "ratio" in metric_lower:
            return "Percentage calculation from operational data"
        if "satisfaction" in metric_lower or "score" in metric_lower or "nps" in metric_lower:
            return "Surveys, user feedback, and NPS measurement"
        if "record" in metric_lower or "paper" in metric_lower or "manual" in metric_lower:
            return "Process audit and workflow compliance checks"
        return "Periodic management reporting and KPI review"

    # ------------------------------------------------------------------
    # ID generators
    # ------------------------------------------------------------------

    def _next_plan_id(self) -> str:
        pid = f"BTP-{self._plan_counter:04d}"
        self._plan_counter += 1
        return pid

    def _next_obj_id(self) -> str:
        oid = f"OBJ-{self._obj_counter:04d}"
        self._obj_counter += 1
        return oid

    def _next_kpi_id(self) -> str:
        kid = f"KPI-{self._kpi_counter:04d}"
        self._kpi_counter += 1
        return kid

    def _next_impact_id(self) -> str:
        iid = f"IMP-{self._impact_counter:04d}"
        self._impact_counter += 1
        return iid

    def _next_phase_id(self) -> str:
        phid = f"PHS-{self._phase_counter:04d}"
        self._phase_counter += 1
        return phid
