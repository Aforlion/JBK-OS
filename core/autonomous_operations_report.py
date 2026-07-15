"""Specification 041 — Autonomous Company Mode: AutonomousAction, OperationalCycle,
and AutonomousOperationsReport domain models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.company_health_snapshot import CompanyHealthSnapshot


class ActionStatus(str):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"


class AutonomousAction:
    """Records a single autonomous action taken (or blocked) by the engine.

    Every action — whether executed, blocked, or escalated — is recorded
    unconditionally to support BR-041-013 (Explainability) and
    BR-041-015 (Continuous Audit).
    """

    def __init__(
        self,
        engine: str,
        action_type: str,
        reasoning: str,
        confidence: float = 1.0,
        authorization_required: bool = False,
        status: str = "EXECUTED",
        action_id: str | None = None,
        evidence: list[str] | None = None,
        outcome: str | None = None,
    ) -> None:
        if not engine:
            raise ValueError("Engine is required.")
        if not action_type:
            raise ValueError("Action type is required.")

        self.action_id: str = action_id or f"ACT-{uuid.uuid4().hex[:8].upper()}"
        self.timestamp: str = datetime.now(timezone.utc).isoformat()
        self.engine: str = engine
        self.action_type: str = action_type
        self.reasoning: str = reasoning
        self.confidence: float = max(0.0, min(1.0, float(confidence)))
        self.authorization_required: bool = authorization_required
        self.status: str = status
        self.evidence: list[str] = list(evidence or [])
        self.outcome: str | None = outcome

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "timestamp": self.timestamp,
            "engine": self.engine,
            "action_type": self.action_type,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "authorization_required": self.authorization_required,
            "status": self.status,
            "evidence": self.evidence,
            "outcome": self.outcome,
        }

    def __repr__(self) -> str:
        return (
            f"<AutonomousAction id={self.action_id!r} type={self.action_type!r} "
            f"status={self.status!r} auth_required={self.authorization_required}>"
        )


class OperationalCycle:
    """Tracks the complete record of one autonomous operational cycle.

    Every run of ``AutonomousOperationsEngine.run_operational_cycle()``
    produces exactly one OperationalCycle.
    """

    def __init__(
        self,
        mission_id: str,
        operational_mode: str,
        cycle_id: str | None = None,
    ) -> None:
        self.cycle_id: str = cycle_id or f"CYC-{uuid.uuid4().hex[:8].upper()}"
        self.mission_id: str = mission_id
        self.operational_mode: str = operational_mode
        self.start_time: str = datetime.now(timezone.utc).isoformat()
        self.end_time: str | None = None

        # Populated during the cycle phases
        self.observations: dict[str, Any] = {}
        self.actions: list[AutonomousAction] = []
        self.decisions: list[str] = []
        self.outcomes: list[str] = []

    def close(self) -> None:
        self.end_time = datetime.now(timezone.utc).isoformat()

    def add_action(self, action: AutonomousAction) -> None:
        self.actions.append(action)

    def add_decision(self, decision: str) -> None:
        self.decisions.append(decision)

    def add_outcome(self, outcome: str) -> None:
        self.outcomes.append(outcome)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "mission_id": self.mission_id,
            "operational_mode": self.operational_mode,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "observations": self.observations,
            "actions": [a.to_dict() for a in self.actions],
            "decisions": self.decisions,
            "outcomes": self.outcomes,
        }

    def __repr__(self) -> str:
        return (
            f"<OperationalCycle id={self.cycle_id!r} "
            f"mode={self.operational_mode!r} actions={len(self.actions)}>"
        )


class AutonomousOperationsReport:
    """Full output of one autonomous operational cycle.

    Produced at the end of ``run_operational_cycle()``.  Contains the
    cycle record, company health, mission progress, prioritised action
    lists, escalations, recommendations, and a complete audit trail.
    """

    def __init__(
        self,
        cycle: OperationalCycle,
        company_health: CompanyHealthSnapshot,
        mission_progress: dict[str, Any],
        completed_actions: list[AutonomousAction],
        pending_actions: list[AutonomousAction],
        blocked_actions: list[AutonomousAction],
        escalations: list[str],
        recommendations: list[str],
        report_id: str | None = None,
    ) -> None:
        self.report_id: str = report_id or f"AOR-{uuid.uuid4().hex[:8].upper()}"
        self.generated_at: str = datetime.now(timezone.utc).isoformat()

        self.cycle: OperationalCycle = cycle
        self.company_health: CompanyHealthSnapshot = company_health
        self.mission_progress: dict[str, Any] = mission_progress

        self.completed_actions: list[AutonomousAction] = completed_actions
        self.pending_actions: list[AutonomousAction] = pending_actions
        self.blocked_actions: list[AutonomousAction] = blocked_actions
        self.escalations: list[str] = escalations
        self.recommendations: list[str] = recommendations

        # Immutable audit trail — every action in the cycle, regardless of status
        self.audit_trail: list[dict[str, Any]] = [a.to_dict() for a in cycle.actions]

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "cycle": self.cycle.to_dict(),
            "company_health": self.company_health.to_dict(),
            "mission_progress": self.mission_progress,
            "completed_actions": [a.to_dict() for a in self.completed_actions],
            "pending_actions": [a.to_dict() for a in self.pending_actions],
            "blocked_actions": [a.to_dict() for a in self.blocked_actions],
            "escalations": self.escalations,
            "recommendations": self.recommendations,
            "audit_trail": self.audit_trail,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "cycle_id": self.cycle.cycle_id,
            "operational_mode": self.cycle.operational_mode,
            "company_health": self.company_health.summary(),
            "mission_progress": self.mission_progress,
            "completed": len(self.completed_actions),
            "pending": len(self.pending_actions),
            "blocked": len(self.blocked_actions),
            "escalations": len(self.escalations),
        }

    def __repr__(self) -> str:
        return (
            f"<AutonomousOperationsReport id={self.report_id!r} "
            f"health={self.company_health.status!r} "
            f"completed={len(self.completed_actions)} "
            f"blocked={len(self.blocked_actions)}>"
        )
