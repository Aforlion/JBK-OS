"""Specification 041 — Autonomous Company Mode: CompanyMission domain model."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any


class MissionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MissionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CompanyMission:
    """CEO-defined mission that drives autonomous operational cycles.

    The mission is the north star for the Autonomous Operations Engine.
    All prioritisation, planning, and execution decisions are evaluated
    against registered missions.
    """

    def __init__(
        self,
        objective: str,
        kpis: list[str] | None = None,
        constraints: list[str] | None = None,
        success_criteria: list[str] | None = None,
        priority: MissionPriority | str = MissionPriority.HIGH,
        mission_id: str | None = None,
        status: MissionStatus | str = MissionStatus.ACTIVE,
    ) -> None:
        if not objective or not objective.strip():
            raise ValueError("Mission objective is required.")

        self.mission_id: str = mission_id or f"MSN-{uuid.uuid4().hex[:8].upper()}"
        self.objective: str = objective.strip()
        self.kpis: list[str] = list(kpis or [])
        self.constraints: list[str] = list(constraints or [])
        self.success_criteria: list[str] = list(success_criteria or [])
        self.priority: MissionPriority = (
            priority if isinstance(priority, MissionPriority)
            else MissionPriority(priority)
        )
        self.status: MissionStatus = (
            status if isinstance(status, MissionStatus)
            else MissionStatus(status)
        )

        # Progress tracking — updated by the engine across cycles
        self.progress_percent: float = 0.0
        self.milestones_achieved: list[str] = []
        self.cycles_executed: int = 0

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def pause(self) -> None:
        """Pause an active mission (CEO intervention)."""
        if self.status != MissionStatus.ACTIVE:
            raise ValueError(f"Only ACTIVE missions can be paused. Current: {self.status.value}")
        self.status = MissionStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused mission."""
        if self.status != MissionStatus.PAUSED:
            raise ValueError(f"Only PAUSED missions can be resumed. Current: {self.status.value}")
        self.status = MissionStatus.ACTIVE

    def complete(self) -> None:
        """Mark the mission as completed."""
        self.status = MissionStatus.COMPLETED
        self.progress_percent = 100.0

    def cancel(self) -> None:
        """Cancel the mission."""
        self.status = MissionStatus.CANCELLED

    def record_cycle(self, milestone: str | None = None) -> None:
        """Increment the cycle counter and optionally log a milestone."""
        self.cycles_executed += 1
        if milestone:
            self.milestones_achieved.append(milestone)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "priority": self.priority.value,
            "status": self.status.value,
            "kpis": self.kpis,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
            "progress_percent": self.progress_percent,
            "milestones_achieved": self.milestones_achieved,
            "cycles_executed": self.cycles_executed,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "cycles_executed": self.cycles_executed,
        }

    def __repr__(self) -> str:
        return (
            f"<CompanyMission id={self.mission_id!r} "
            f"priority={self.priority.value} status={self.status.value}>"
        )
