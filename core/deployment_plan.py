from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DeploymentPlan:
    """Defines the ordered steps and rollback strategy for a deployment.

    BR-052-001: Deployments are repeatable (plan is declarative).
    BR-052-008: Fully serializable.
    """

    def __init__(
        self,
        deployment_id: str,
        target_environment: str,
        version: str,
        deployment_steps: list[str] | None = None,
        prerequisites: list[str] | None = None,
        rollback_plan: list[str] | None = None,
        estimated_duration_seconds: int = 60,
        created_at: str | None = None,
    ) -> None:
        self.deployment_id = deployment_id
        self.target_environment = target_environment
        self.version = version
        self.deployment_steps = deployment_steps or []
        self.prerequisites = prerequisites or []
        self.rollback_plan = rollback_plan or []
        self.estimated_duration_seconds = estimated_duration_seconds
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "target_environment": self.target_environment,
            "version": self.version,
            "deployment_steps": self.deployment_steps,
            "prerequisites": self.prerequisites,
            "rollback_plan": self.rollback_plan,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "created_at": self.created_at,
        }
