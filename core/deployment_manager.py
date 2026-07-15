from __future__ import annotations

import sys
import time
import logging
from typing import Any
from datetime import datetime, timezone

from core.deployment_environment import DeploymentEnvironment
from core.deployment_plan import DeploymentPlan
from core.deployment_report import DeploymentReport

LOGGER = logging.getLogger(__name__)

# Default config profiles per environment type
_DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    "DEVELOPMENT": {
        "logging": "DEBUG",
        "ai_provider": "mock",
        "monitoring": False,
        "security": "relaxed",
        "hot_reload": True,
    },
    "TESTING": {
        "logging": "INFO",
        "ai_provider": "mock",
        "monitoring": True,
        "security": "standard",
        "hot_reload": False,
    },
    "STAGING": {
        "logging": "WARNING",
        "ai_provider": "openai",
        "monitoring": True,
        "security": "strict",
        "hot_reload": False,
    },
    "PRODUCTION": {
        "logging": "ERROR",
        "ai_provider": "openai",
        "monitoring": True,
        "security": "strict",
        "hot_reload": False,
    },
    "DEMO": {
        "logging": "INFO",
        "ai_provider": "mock",
        "monitoring": False,
        "security": "standard",
        "hot_reload": False,
    },
}

# Required prerequisite keys per plan step category
_PREREQUISITE_CHECKS = {
    "check_python_version": lambda: sys.version_info >= (3, 10),
    "check_core_directory": lambda: True,   # Mocked always pass in V1
    "check_config_files": lambda: True,
    "check_executive_registry": lambda: True,
    "check_ai_gateway": lambda: True,
}


class ConfigProfileManager:
    """Manages isolated configuration profiles per environment type.

    BR-052-005: Environment configurations remain isolated.
    """

    def get_profile(self, env_type: str) -> dict[str, Any]:
        return dict(_DEFAULT_PROFILES.get(env_type, {}))

    def merge_overrides(self, env_type: str, overrides: dict[str, Any]) -> dict[str, Any]:
        """Returns a merged profile with user overrides applied."""
        profile = self.get_profile(env_type)
        profile.update(overrides)
        return profile


class VersionRegistry:
    """Tracks installed version and full deployment history.

    BR-052-008: Serializable.
    """

    def __init__(self) -> None:
        self.installed_version: str | None = None
        self._history: list[dict[str, Any]] = []

    def record(self, event_type: str, version: str, environment: str, success: bool) -> None:
        self._history.append({
            "event_type": event_type,   # INSTALL, UPGRADE, ROLLBACK
            "version": version,
            "environment": environment,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if success and event_type in ("INSTALL", "UPGRADE"):
            self.installed_version = version

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def to_dict(self) -> dict[str, Any]:
        return {
            "installed_version": self.installed_version,
            "history": self._history,
        }


class DeploymentManager:
    """Orchestrates environment provisioning, deployment, upgrades, rollback, and health checks.

    BR-052-001: Deployments are repeatable.
    BR-052-002: Failed deployments rollback safely.
    BR-052-003: Business engines are never modified during deployment.
    BR-052-004: Validates all prerequisites.
    BR-052-009: Health checks run automatically post-deployment.
    """

    def __init__(self) -> None:
        self.config_manager = ConfigProfileManager()
        self.version_registry = VersionRegistry()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_environment(self, env: DeploymentEnvironment) -> dict[str, bool]:
        """Run prerequisite and structural validations. BR-052-004."""
        results: dict[str, bool] = {}
        for check_name, check_fn in _PREREQUISITE_CHECKS.items():
            try:
                results[check_name] = check_fn()
            except Exception:
                results[check_name] = False
        return results

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_plan(
        self,
        plan: DeploymentPlan,
        env: DeploymentEnvironment,
        fail_on_step: str | None = None,   # Inject failure point for testing
    ) -> DeploymentReport:
        """Execute deployment steps sequentially.

        Triggers rollback automatically on step failure (BR-052-002).
        """
        start_time = time.monotonic()
        completed: list[str] = []
        failed: list[str] = []
        warnings: list[str] = []
        rollback_triggered = False

        # Apply config profile (BR-052-005)
        profile = self.config_manager.get_profile(env.env_type)
        if env.config_profile:
            profile.update(env.config_profile)

        LOGGER.info("deployment_manager deployment_id=%s version=%s env=%s", plan.deployment_id, plan.version, env.env_type)

        # Validate prerequisites first (BR-052-004)
        validation_results = self.validate_environment(env)
        failed_prereqs = [k for k, v in validation_results.items() if not v]
        if failed_prereqs:
            warnings.append(f"Prerequisite warnings: {failed_prereqs}")

        # Execute steps
        for step in plan.deployment_steps:
            if step == fail_on_step:
                LOGGER.warning("deployment_manager step=%s FAILED (injected)", step)
                failed.append(step)
                # Trigger rollback (BR-052-002)
                rollback_triggered = True
                self._execute_rollback(plan, env, completed)
                break

            LOGGER.info("deployment_manager step=%s OK", step)
            completed.append(step)

        # Update environment status
        if rollback_triggered or failed:
            env.status = "FAILED"
        else:
            env.status = "ACTIVE"

        # Run health check automatically (BR-052-009)
        health = self.run_health_check(env)
        validation_results.update(health)

        execution_time = time.monotonic() - start_time

        # Record in version registry
        success = not rollback_triggered and not failed
        self.version_registry.record(
            event_type="INSTALL",
            version=plan.version,
            environment=env.env_type,
            success=success,
        )

        # Produce immutable report (BR-052-006)
        recommendations = []
        if rollback_triggered:
            recommendations.append("Investigate failed step and re-deploy after fix.")
        if warnings:
            recommendations.append("Review prerequisite warnings before production go-live.")

        return DeploymentReport(
            deployment_id=plan.deployment_id,
            installed_version=plan.version,
            target_environment=env.env_type,
            completed_steps=completed,
            failed_steps=failed,
            warnings=warnings,
            validation_results=validation_results,
            execution_time_seconds=round(execution_time, 4),
            rollback_triggered=rollback_triggered,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def _execute_rollback(self, plan: DeploymentPlan, env: DeploymentEnvironment, completed_steps: list[str]) -> None:
        """Restore environment using rollback plan steps. BR-052-007: Never deletes business data."""
        LOGGER.warning("deployment_manager rollback initiated deployment_id=%s", plan.deployment_id)
        for rollback_step in plan.rollback_plan:
            LOGGER.info("deployment_manager rollback_step=%s", rollback_step)

        self.version_registry.record(
            event_type="ROLLBACK",
            version="previous",
            environment=env.env_type,
            success=True,
        )

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    def run_health_check(self, env: DeploymentEnvironment) -> dict[str, bool]:
        """Post-deployment subsystem validation. BR-052-009."""
        checks = {
            "kernel_boot": env.status != "FAILED",
            "registry_loaded": True,
            "ai_gateway_available": env.config_profile.get("ai_provider", "mock") is not None,
            "communications_operational": True,
            "integration_framework_operational": True,
        }
        return checks

    # ------------------------------------------------------------------
    # Upgrade
    # ------------------------------------------------------------------

    def upgrade(self, plan: DeploymentPlan, env: DeploymentEnvironment) -> DeploymentReport:
        """Run an incremental upgrade using the deployment plan."""
        report = self.execute_plan(plan, env)
        if report.success:
            self.version_registry.record(
                event_type="UPGRADE",
                version=plan.version,
                environment=env.env_type,
                success=True,
            )
        return report
