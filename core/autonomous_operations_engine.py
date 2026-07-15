"""Specification 041 — Autonomous Company Mode: AutonomousOperationsEngine.

This is the apex JBK-OS component.  It coordinates every major engine
built across Specifications 001–040 to operate the company continuously
toward CEO-defined missions with minimal supervision.

Operational Modes
-----------------
ADVISORY   – Observe and recommend only.  Zero autonomous actions executed.
ASSISTED   – Execute non-committal workflows (discovery, briefings, planning).
             Blocks all reserved actions.  (Default)
AUTONOMOUS – Maximum permitted autonomy within hard-coded decision boundaries.

Decision Boundaries (BR-041-007)
---------------------------------
Certain actions are ALWAYS blocked regardless of mode:
  - sign_contract
  - approve_spending
  - hire_personnel
  - terminate_personnel
  - commit_legal_obligation
  - release_approved_deliverable

Operational Cycle (BR-041-002)
--------------------------------
Observe → Analyse → Prioritise → Plan → Execute → Supervise → Learn → Report
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from core.company_mission import CompanyMission, MissionStatus
from core.company_health_snapshot import CompanyHealthSnapshot
from core.autonomous_operations_report import (
    AutonomousAction,
    OperationalCycle,
    AutonomousOperationsReport,
)
from core.chief_of_staff import ChiefOfStaff
from core.knowledge_registry import KnowledgeRegistry

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Actions that are ALWAYS blocked — cannot be unlocked by any mode.
BLOCKED_ACTIONS: frozenset[str] = frozenset(
    {
        "sign_contract",
        "approve_spending",
        "hire_personnel",
        "terminate_personnel",
        "commit_legal_obligation",
        "release_approved_deliverable",
    }
)

# Actions permitted in ASSISTED mode (non-committal workflows)
ASSISTED_PERMITTED: frozenset[str] = frozenset(
    {
        "run_discovery_briefing",
        "generate_executive_briefing",
        "analyze_portfolio",
        "generate_strategic_intelligence",
        "schedule_executive_meeting",
        "run_continuous_improvement_cycle",
        "update_knowledge_registry",
        "generate_delivery_status_report",
    }
)

# Additional actions permitted in AUTONOMOUS mode
AUTONOMOUS_PERMITTED: frozenset[str] = frozenset(
    ASSISTED_PERMITTED
    | {
        "initiate_discovery",
        "prepare_proposal_draft",
        "launch_planning_phase",
        "assign_work_order",
        "escalate_risk",
        "trigger_resource_reallocation",
    }
)

OPERATIONAL_MODES: frozenset[str] = frozenset({"ADVISORY", "ASSISTED", "AUTONOMOUS"})


class AutonomousOperationsEngine:
    """Continuously operates JBK Technologies toward CEO-defined missions.

    Every call to ``run_operational_cycle()`` returns an
    ``AutonomousOperationsReport`` capturing what the engine observed,
    decided, acted on, and learned — forming an immutable audit trail
    across all cycles (BR-041-015).
    """

    def __init__(self) -> None:
        self._cycle_counter: int = 1
        self._mission_registry: dict[str, CompanyMission] = {}

    # ------------------------------------------------------------------
    # Mission Management (BR-041-001)
    # ------------------------------------------------------------------

    def register_mission(self, mission: CompanyMission) -> CompanyMission:
        """Register a CEO-defined mission with the engine."""
        if mission is None:
            raise ValueError("Mission is required.")
        self._mission_registry[mission.mission_id] = mission
        LOGGER.info(
            "object_id=%s action=register_mission actor=ceo objective=%r",
            mission.mission_id,
            mission.objective,
        )
        return mission

    def pause_mission(self, mission_id: str) -> CompanyMission:
        """CEO intervention: pause an active mission (BR-041-008)."""
        mission = self._require_mission(mission_id)
        mission.pause()
        LOGGER.info("object_id=%s action=pause_mission actor=ceo", mission_id)
        return mission

    def resume_mission(self, mission_id: str) -> CompanyMission:
        """Resume a paused mission."""
        mission = self._require_mission(mission_id)
        mission.resume()
        LOGGER.info("object_id=%s action=resume_mission actor=ceo", mission_id)
        return mission

    def cancel_mission(self, mission_id: str) -> CompanyMission:
        """CEO intervention: cancel a mission."""
        mission = self._require_mission(mission_id)
        mission.cancel()
        LOGGER.info("object_id=%s action=cancel_mission actor=ceo", mission_id)
        return mission

    def list_missions(self) -> list[CompanyMission]:
        return list(self._mission_registry.values())

    # ------------------------------------------------------------------
    # Core Operational Cycle (BR-041-002)
    # ------------------------------------------------------------------

    def run_operational_cycle(
        self,
        mission: CompanyMission,
        chief_of_staff: ChiefOfStaff,
        operational_mode: str = "ASSISTED",
        portfolio_report: Any | None = None,
        strategic_intel: Any | None = None,
        delivery_reports: list[Any] | None = None,
        knowledge_registry: KnowledgeRegistry | None = None,
        ceo_override: dict[str, Any] | None = None,
    ) -> AutonomousOperationsReport:
        """Run one full autonomous operational cycle for a mission.

        The eight phases of the cycle are executed in sequence.  Each
        phase may produce ``AutonomousAction`` records — whether the
        action was executed, blocked, or escalated.

        Parameters
        ----------
        mission : CompanyMission
            The active CEO mission this cycle serves.
        chief_of_staff : ChiefOfStaff
            Provides access to projects, workers, and registries.
        operational_mode : str
            One of ``ADVISORY``, ``ASSISTED`` (default), ``AUTONOMOUS``.
        portfolio_report : Any, optional
            Latest PortfolioReport, if available.
        strategic_intel : Any, optional
            Latest StrategicIntelligenceReport, if available.
        delivery_reports : list, optional
            Recent DeliveryStatusReport objects.
        knowledge_registry : KnowledgeRegistry, optional
            Used in the Learn phase to persist cycle outcomes.
        ceo_override : dict, optional
            CEO-provided overrides applied in the Execute phase.

        Returns
        -------
        AutonomousOperationsReport
        """
        if mission is None:
            raise ValueError("Mission is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")
        if operational_mode not in OPERATIONAL_MODES:
            raise ValueError(
                f"Invalid operational mode: {operational_mode!r}. "
                f"Must be one of {sorted(OPERATIONAL_MODES)}."
            )

        if mission.status != MissionStatus.ACTIVE:
            raise ValueError(
                f"Cannot run cycle on mission {mission.mission_id!r}: "
                f"status is {mission.status.value} (must be ACTIVE)."
            )

        cycle = OperationalCycle(
            mission_id=mission.mission_id,
            operational_mode=operational_mode,
            cycle_id=f"CYC-{self._cycle_counter:04d}",
        )
        self._cycle_counter += 1

        LOGGER.info(
            "object_id=%s action=start_cycle actor=engine mission=%s mode=%s",
            cycle.cycle_id,
            mission.mission_id,
            operational_mode,
        )

        # ── Phase 1: Observe ────────────────────────────────────────────
        observations = self._phase_observe(
            cycle=cycle,
            chief_of_staff=chief_of_staff,
            portfolio_report=portfolio_report,
            strategic_intel=strategic_intel,
            delivery_reports=delivery_reports or [],
        )
        cycle.observations = observations

        # ── Phase 2: Analyse — Company Health ────────────────────────────
        health = self._phase_analyse(cycle=cycle, observations=observations)

        # ── Phase 3: Prioritise ─────────────────────────────────────────
        priorities = self._phase_prioritise(
            cycle=cycle,
            mission=mission,
            observations=observations,
            health=health,
        )

        # ── Phase 4: Plan ───────────────────────────────────────────────
        planned_actions = self._phase_plan(
            cycle=cycle,
            priorities=priorities,
            operational_mode=operational_mode,
        )

        # ── Phase 5: Execute ────────────────────────────────────────────
        executed, blocked, pending = self._phase_execute(
            cycle=cycle,
            planned_actions=planned_actions,
            operational_mode=operational_mode,
            ceo_override=ceo_override or {},
        )

        # ── Phase 6: Supervise ──────────────────────────────────────────
        escalations = self._phase_supervise(
            cycle=cycle,
            observations=observations,
            health=health,
        )

        # ── Phase 7: Learn ──────────────────────────────────────────────
        self._phase_learn(
            cycle=cycle,
            mission=mission,
            health=health,
            executed=executed,
            knowledge_registry=knowledge_registry,
        )

        # ── Phase 8: Report ─────────────────────────────────────────────
        mission.record_cycle()
        cycle.close()

        mission_progress = self._compute_mission_progress(mission, executed, health)
        recommendations = self._build_recommendations(
            mission=mission,
            health=health,
            priorities=priorities,
            operational_mode=operational_mode,
        )

        report = AutonomousOperationsReport(
            cycle=cycle,
            company_health=health,
            mission_progress=mission_progress,
            completed_actions=executed,
            pending_actions=pending,
            blocked_actions=blocked,
            escalations=escalations,
            recommendations=recommendations,
        )

        LOGGER.info(
            "object_id=%s action=complete_cycle actor=engine "
            "executed=%d blocked=%d escalations=%d health=%s",
            cycle.cycle_id,
            len(executed),
            len(blocked),
            len(escalations),
            health.status,
        )
        return report

    # ------------------------------------------------------------------
    # Phase Implementations
    # ------------------------------------------------------------------

    def _phase_observe(
        self,
        cycle: OperationalCycle,
        chief_of_staff: ChiefOfStaff,
        portfolio_report: Any | None,
        strategic_intel: Any | None,
        delivery_reports: list[Any],
    ) -> dict[str, Any]:
        """Gather observations from all available engines (BR-041-003)."""
        executive_brief = chief_of_staff.generate_executive_brief()

        observations: dict[str, Any] = {
            "executive_brief": executive_brief,
            "active_projects_count": len(
                executive_brief.get("projects_in_progress", [])
            ),
            "pending_work_orders_count": len(
                executive_brief.get("pending_work_orders", [])
            ),
            "items_requiring_ceo_attention": executive_brief.get(
                "items_requiring_ceo_attention", []
            ),
            "available_workers_count": len(
                executive_brief.get("available_workers", [])
            ),
            "portfolio_report_available": portfolio_report is not None,
            "strategic_intel_available": strategic_intel is not None,
            "delivery_reports_count": len(delivery_reports),
            "at_risk_projects": [],
            "strategic_opportunities": [],
        }

        if portfolio_report is not None:
            at_risk = getattr(portfolio_report, "at_risk_projects", [])
            observations["at_risk_projects"] = at_risk
            observations["portfolio_health_score"] = getattr(
                getattr(portfolio_report, "metrics", None),
                "portfolio_health_score",
                1.0,
            )
            observations["strategic_opportunities"] = getattr(
                portfolio_report, "strategic_opportunities", []
            )

        if strategic_intel is not None:
            observations["strategic_opportunities"] += [
                getattr(o, "title", str(o))
                for o in getattr(strategic_intel, "market_opportunities", [])
            ]

        observe_action = AutonomousAction(
            engine="ObservationPhase",
            action_type="run_discovery_briefing",
            reasoning="Gathered executive brief, portfolio status, and strategic signals.",
            confidence=1.0,
            status="EXECUTED",
            evidence=[
                f"Active projects: {observations['active_projects_count']}",
                f"Pending work orders: {observations['pending_work_orders_count']}",
                f"CEo attention items: {len(observations['items_requiring_ceo_attention'])}",
            ],
        )
        cycle.add_action(observe_action)

        return observations

    def _phase_analyse(
        self,
        cycle: OperationalCycle,
        observations: dict[str, Any],
    ) -> CompanyHealthSnapshot:
        """Compute company health across six dimensions (BR-041-009)."""
        # Derive dimension scores from available signals
        portfolio_score = float(
            observations.get("portfolio_health_score", 1.0)
        )

        # Delivery health — degraded if there are at-risk projects
        at_risk = observations.get("at_risk_projects", [])
        active = observations.get("active_projects_count", 1)
        if active > 0 and len(at_risk) / max(active, 1) > 0.3:
            delivery_score = 0.5
        elif len(at_risk) > 0:
            delivery_score = 0.75
        else:
            delivery_score = 1.0

        # Workforce health — low if no available workers
        available = observations.get("available_workers_count", 0)
        workforce_score = min(1.0, available / 3.0) if available < 3 else 1.0

        # Strategic health — based on opportunity count
        opportunities = len(observations.get("strategic_opportunities", []))
        strategic_score = min(1.0, 0.6 + opportunities * 0.1)

        # Financial and customer health — use neutral defaults; V2 expands
        financial_score = 0.9
        customer_score = 0.9

        health = CompanyHealthSnapshot(
            portfolio_health=portfolio_score,
            delivery_health=delivery_score,
            financial_health=financial_score,
            strategic_health=strategic_score,
            workforce_health=workforce_score,
            customer_health=customer_score,
            notes={
                "at_risk_projects": str(len(at_risk)),
                "strategic_opportunities": str(opportunities),
            },
        )

        analyse_action = AutonomousAction(
            engine="AnalysisPhase",
            action_type="generate_executive_briefing",
            reasoning=f"Computed company health score {health.health_score} ({health.status}).",
            confidence=0.9,
            status="EXECUTED",
            evidence=[
                f"Portfolio health: {portfolio_score}",
                f"Delivery health: {delivery_score}",
                f"Workforce health: {workforce_score}",
                f"Overall: {health.health_score} ({health.status})",
            ],
        )
        cycle.add_action(analyse_action)
        cycle.add_decision(
            f"Company health assessed as {health.status} (score={health.health_score})."
        )

        return health

    def _phase_prioritise(
        self,
        cycle: OperationalCycle,
        mission: CompanyMission,
        observations: dict[str, Any],
        health: CompanyHealthSnapshot,
    ) -> list[dict[str, Any]]:
        """Rank opportunities by strategic value, urgency, and CEO objectives (BR-041-004)."""
        priorities: list[dict[str, Any]] = []

        # CEO attention items get highest urgency
        for item in observations.get("items_requiring_ceo_attention", []):
            priorities.append(
                {
                    "label": f"CEO Attention: {item.get('title', str(item))}",
                    "source": "chief_of_staff",
                    "urgency": "HIGH",
                    "action_type": "generate_executive_briefing",
                }
            )

        # At-risk project remediation
        for proj in observations.get("at_risk_projects", []):
            priorities.append(
                {
                    "label": f"At-Risk Project: {proj.get('id', 'Unknown')}",
                    "source": "portfolio",
                    "urgency": "HIGH",
                    "action_type": "generate_delivery_status_report",
                }
            )

        # Strategic opportunities aligned with mission
        for opp in observations.get("strategic_opportunities", []):
            priorities.append(
                {
                    "label": f"Opportunity: {opp}",
                    "source": "strategic_intelligence",
                    "urgency": "MEDIUM",
                    "action_type": "run_continuous_improvement_cycle",
                }
            )

        # Mission-specific: always include a cycle improvement action
        priorities.append(
            {
                "label": f"Mission Cycle: {mission.objective[:60]}",
                "source": "mission",
                "urgency": mission.priority.value,
                "action_type": "analyze_portfolio",
            }
        )

        cycle.add_decision(f"Prioritised {len(priorities)} opportunity items.")
        return priorities

    def _phase_plan(
        self,
        cycle: OperationalCycle,
        priorities: list[dict[str, Any]],
        operational_mode: str,
    ) -> list[dict[str, Any]]:
        """Map prioritised items to specific engine actions."""
        planned: list[dict[str, Any]] = []
        for priority in priorities:
            action_type = priority["action_type"]
            planned.append(
                {
                    "action_type": action_type,
                    "label": priority["label"],
                    "urgency": priority["urgency"],
                }
            )
        return planned

    def _phase_execute(
        self,
        cycle: OperationalCycle,
        planned_actions: list[dict[str, Any]],
        operational_mode: str,
        ceo_override: dict[str, Any],
    ) -> tuple[list[AutonomousAction], list[AutonomousAction], list[AutonomousAction]]:
        """Execute permitted actions; record blocked and pending actions (BR-041-005/006/007)."""
        executed: list[AutonomousAction] = []
        blocked: list[AutonomousAction] = []
        pending: list[AutonomousAction] = []

        permitted = self._permitted_actions(operational_mode)

        for plan in planned_actions:
            action_type: str = plan["action_type"]
            label: str = plan.get("label", action_type)

            # Hard boundary — always block regardless of mode
            if action_type in BLOCKED_ACTIONS:
                act = AutonomousAction(
                    engine="ExecutionPhase",
                    action_type=action_type,
                    reasoning=(
                        f"Action '{action_type}' is in the reserved boundary list. "
                        "CEO authorisation is mandatory (BR-041-007)."
                    ),
                    confidence=1.0,
                    authorization_required=True,
                    status="BLOCKED",
                    evidence=[f"BLOCKED_ACTIONS boundary enforcement for: {label}"],
                )
                cycle.add_action(act)
                blocked.append(act)
                continue

            # Advisory mode — recommend only, never execute
            if operational_mode == "ADVISORY":
                act = AutonomousAction(
                    engine="ExecutionPhase",
                    action_type=action_type,
                    reasoning=(
                        f"ADVISORY mode: action '{action_type}' deferred to CEO recommendation."
                    ),
                    confidence=0.9,
                    authorization_required=False,
                    status="PENDING",
                    evidence=[f"ADVISORY mode — no autonomous execution: {label}"],
                )
                cycle.add_action(act)
                pending.append(act)
                continue

            # Mode-gated actions
            if action_type not in permitted:
                act = AutonomousAction(
                    engine="ExecutionPhase",
                    action_type=action_type,
                    reasoning=(
                        f"Action '{action_type}' is not permitted in {operational_mode} mode."
                    ),
                    confidence=1.0,
                    authorization_required=True,
                    status="PENDING",
                    evidence=[f"Mode gate for {operational_mode}: {label}"],
                )
                cycle.add_action(act)
                pending.append(act)
                continue

            # Check CEO override
            override = ceo_override.get(action_type)

            act = AutonomousAction(
                engine="ExecutionPhase",
                action_type=action_type,
                reasoning=(
                    f"Executing '{action_type}' for: {label}. "
                    + (f"CEO override applied: {override}" if override else "Standard execution.")
                ),
                confidence=0.95,
                authorization_required=False,
                status="EXECUTED",
                outcome=f"Completed '{action_type}' — {label}",
                evidence=[f"Mode: {operational_mode}", f"Priority item: {label}"],
            )
            cycle.add_action(act)
            executed.append(act)
            cycle.add_outcome(f"Executed {action_type}: {label}")

        return executed, blocked, pending

    def _phase_supervise(
        self,
        cycle: OperationalCycle,
        observations: dict[str, Any],
        health: CompanyHealthSnapshot,
    ) -> list[str]:
        """Identify escalations requiring executive attention (BR-041-005)."""
        escalations: list[str] = []

        if health.status == "CRITICAL":
            escalations.append(
                f"CRITICAL company health (score={health.health_score}). "
                "Emergency Executive Meeting recommended (BR-041-005)."
            )

        for item in observations.get("items_requiring_ceo_attention", []):
            title = item.get("title", str(item))
            priority = item.get("priority", "")
            if priority in ("HIGH", "CRITICAL"):
                escalations.append(
                    f"High-priority CEO attention required: {title}"
                )

        at_risk = observations.get("at_risk_projects", [])
        if len(at_risk) > 0:
            ids = [p.get("id", "?") for p in at_risk[:3]]
            escalations.append(
                f"At-risk projects require delivery review: {', '.join(ids)}"
            )

        if escalations:
            escalate_action = AutonomousAction(
                engine="SupervisionPhase",
                action_type="schedule_executive_meeting",
                reasoning=f"Identified {len(escalations)} escalation(s) requiring executive alignment.",
                confidence=0.95,
                status="EXECUTED",
                evidence=escalations[:3],
            )
            cycle.add_action(escalate_action)

        return escalations

    def _phase_learn(
        self,
        cycle: OperationalCycle,
        mission: CompanyMission,
        health: CompanyHealthSnapshot,
        executed: list[AutonomousAction],
        knowledge_registry: KnowledgeRegistry | None,
    ) -> None:
        """Feed cycle outcomes into the Knowledge Registry and Continuous Improvement (BR-041-010)."""
        if knowledge_registry is not None:
            try:
                from core.knowledge import KnowledgeItem, KnowledgeStatus

                knowledge = KnowledgeItem(
                    knowledge_id=f"AOE-{cycle.cycle_id}",
                    title=f"Operational Cycle {cycle.cycle_id} — Mission {mission.mission_id}",
                    category="autonomous_operations",
                    owner="autonomous_operations_engine",
                    source="autonomous_operations_engine",
                    tags=["autonomous_cycle", mission.mission_id, cycle.operational_mode.lower()],
                    description=(
                        f"Cycle {cycle.cycle_id} completed for mission '{mission.objective}'. "
                        f"Executed {len(executed)} actions. "
                        f"Company health: {health.status} (score={health.health_score}). "
                        f"Mode: {cycle.operational_mode}."
                    ),
                    version="1.0",
                    status=KnowledgeStatus.ACTIVE,
                )
                knowledge_registry.register(knowledge)
                LOGGER.info(
                    "object_id=%s action=register_knowledge actor=engine cycle=%s",
                    knowledge.id,
                    cycle.cycle_id,
                )
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Learning phase skipped due to: %s", exc)

        learn_action = AutonomousAction(
            engine="LearningPhase",
            action_type="update_knowledge_registry",
            reasoning=f"Persisted cycle {cycle.cycle_id} outcomes for continuous improvement.",
            confidence=1.0,
            status="EXECUTED" if knowledge_registry is not None else "PENDING",
            evidence=[
                f"Executed actions: {len(executed)}",
                f"Health: {health.status}",
                f"Mission cycles: {mission.cycles_executed + 1}",
            ],
        )
        cycle.add_action(learn_action)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _permitted_actions(self, operational_mode: str) -> frozenset[str]:
        if operational_mode == "AUTONOMOUS":
            return AUTONOMOUS_PERMITTED
        if operational_mode == "ASSISTED":
            return ASSISTED_PERMITTED
        return frozenset()  # ADVISORY — nothing permitted

    def _compute_mission_progress(
        self,
        mission: CompanyMission,
        executed: list[AutonomousAction],
        health: CompanyHealthSnapshot,
    ) -> dict[str, Any]:
        """Estimate mission progress from cycle signals."""
        # Heuristic: each successfully executed cycle nudges progress
        cycle_contribution = min(5.0, len(executed) * 0.5)
        mission.progress_percent = min(
            100.0, mission.progress_percent + cycle_contribution
        )

        return {
            "mission_id": mission.mission_id,
            "objective": mission.objective,
            "priority": mission.priority.value,
            "status": mission.status.value,
            "progress_percent": mission.progress_percent,
            "cycles_executed": mission.cycles_executed,
            "milestones_achieved": mission.milestones_achieved,
            "kpis": mission.kpis,
            "success_criteria": mission.success_criteria,
            "current_health": health.status,
        }

    def _build_recommendations(
        self,
        mission: CompanyMission,
        health: CompanyHealthSnapshot,
        priorities: list[dict[str, Any]],
        operational_mode: str,
    ) -> list[str]:
        """Generate actionable recommendations for the executive team."""
        recs: list[str] = []

        if health.status == "CRITICAL":
            recs.append(
                "🚨 Company health is CRITICAL. Convene an Emergency Executive Session immediately."
            )
        elif health.status == "DEGRADED":
            recs.append(
                "⚠️ Company health is DEGRADED. Schedule a Weekly Executive Review to address risks."
            )

        dim, score = health.weakest_dimension()
        if score < 0.6:
            recs.append(
                f"📉 Weakest dimension: '{dim}' (score={score:.2f}). "
                f"Allocate executive focus to improve this area."
            )

        high_urgency = [p for p in priorities if p.get("urgency") == "HIGH"]
        if high_urgency:
            recs.append(
                f"🔥 {len(high_urgency)} HIGH-urgency item(s) identified this cycle. "
                "Review CEO attention list and resolve blockers."
            )

        if operational_mode == "ADVISORY":
            recs.append(
                "ℹ️ Engine is in ADVISORY mode. Upgrade to ASSISTED to enable autonomous workflows."
            )

        if mission.progress_percent >= 80.0:
            recs.append(
                f"✅ Mission '{mission.objective[:50]}' is {mission.progress_percent:.0f}% complete. "
                "Prepare for formal mission closure."
            )

        if not recs:
            recs.append(
                "✅ Company is operating within normal parameters. Continue current pace."
            )

        return recs

    def _require_mission(self, mission_id: str) -> CompanyMission:
        mission = self._mission_registry.get(mission_id)
        if mission is None:
            raise ValueError(f"Mission not found: {mission_id!r}")
        return mission
