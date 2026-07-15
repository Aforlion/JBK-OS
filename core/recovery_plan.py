from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class RecoveryPlan:
    """Defines what to restore, how, and the rollback strategy.

    BR-054-005: Recovery is fully auditable.
    """

    def __init__(
        self,
        recovery_id: str,
        target_snapshot_id: str,
        recovery_scope: list[str],       # e.g. ["REGISTRY", "CONFIGURATION"]
        estimated_duration_seconds: int = 60,
        validation_steps: list[str] | None = None,
        rollback_strategy: list[str] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.recovery_id = recovery_id
        self.target_snapshot_id = target_snapshot_id
        self.recovery_scope = recovery_scope
        self.estimated_duration_seconds = estimated_duration_seconds
        self.validation_steps = validation_steps or []
        self.rollback_strategy = rollback_strategy or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "target_snapshot_id": self.target_snapshot_id,
            "recovery_scope": self.recovery_scope,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "validation_steps": self.validation_steps,
            "rollback_strategy": self.rollback_strategy,
            "created_at": self.created_at,
        }
