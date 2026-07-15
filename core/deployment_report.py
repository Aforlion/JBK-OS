from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DeploymentReport:
    """Immutable post-deployment summary record.

    BR-052-006: Deployment reports are immutable.
    BR-052-008: Fully serializable.
    BR-052-010: Deployment remains explainable.
    """

    _FROZEN = False

    def __init__(
        self,
        deployment_id: str,
        installed_version: str,
        target_environment: str,
        completed_steps: list[str],
        failed_steps: list[str],
        warnings: list[str],
        validation_results: dict[str, bool],
        execution_time_seconds: float,
        rollback_triggered: bool = False,
        recommendations: list[str] | None = None,
        generated_at: str | None = None,
    ) -> None:
        self.deployment_id = deployment_id
        self.installed_version = installed_version
        self.target_environment = target_environment
        self.completed_steps = completed_steps
        self.failed_steps = failed_steps
        self.warnings = warnings
        self.validation_results = validation_results
        self.execution_time_seconds = execution_time_seconds
        self.rollback_triggered = rollback_triggered
        self.recommendations = recommendations or []
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        # Freeze after initialisation
        self._FROZEN = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_FROZEN", False):
            raise AttributeError(f"DeploymentReport is immutable. Cannot set '{name}'.")
        super().__setattr__(name, value)

    @property
    def success(self) -> bool:
        return len(self.failed_steps) == 0 and not self.rollback_triggered

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "installed_version": self.installed_version,
            "target_environment": self.target_environment,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "warnings": self.warnings,
            "validation_results": self.validation_results,
            "execution_time_seconds": self.execution_time_seconds,
            "rollback_triggered": self.rollback_triggered,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
            "success": self.success,
        }
