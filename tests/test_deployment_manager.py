from __future__ import annotations

import unittest

from core.deployment_environment import DeploymentEnvironment, ENVIRONMENT_TYPES
from core.deployment_plan import DeploymentPlan
from core.deployment_report import DeploymentReport
from core.deployment_manager import DeploymentManager, ConfigProfileManager, VersionRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dev_env(**kwargs) -> DeploymentEnvironment:
    return DeploymentEnvironment("ENV-001", "DEVELOPMENT", **kwargs)


def _prod_env(**kwargs) -> DeploymentEnvironment:
    return DeploymentEnvironment("ENV-002", "PRODUCTION", **kwargs)


def _standard_plan(fail_on: str | None = None) -> DeploymentPlan:
    return DeploymentPlan(
        deployment_id="DEPLOY-001",
        target_environment="DEVELOPMENT",
        version="1.0.0",
        deployment_steps=["check_prerequisites", "install_core", "apply_config", "run_migrations", "verify_install"],
        prerequisites=["check_python_version", "check_core_directory"],
        rollback_plan=["restore_config", "restore_registry"],
        estimated_duration_seconds=30,
    )


# ---------------------------------------------------------------------------
# DeploymentEnvironment Tests
# ---------------------------------------------------------------------------

class TestDeploymentEnvironment(unittest.TestCase):

    def test_valid_environment_creation(self) -> None:
        env = _dev_env()
        self.assertEqual(env.env_type, "DEVELOPMENT")
        self.assertEqual(env.status, "PENDING")

    def test_all_environment_types_valid(self) -> None:
        for env_type in ENVIRONMENT_TYPES:
            env = DeploymentEnvironment(f"ENV-{env_type}", env_type)
            self.assertEqual(env.env_type, env_type)

    def test_invalid_env_type_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DeploymentEnvironment("ENV-BAD", "LEGACY")

    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DeploymentEnvironment("ENV-BAD", "DEVELOPMENT", status="UNKNOWN")

    def test_environment_serialization(self) -> None:
        """BR-052-008: Environment is serializable."""
        d = _dev_env().to_dict()
        self.assertEqual(d["env_type"], "DEVELOPMENT")
        self.assertIn("created_at", d)
        self.assertIn("config_profile", d)


# ---------------------------------------------------------------------------
# DeploymentPlan Tests
# ---------------------------------------------------------------------------

class TestDeploymentPlan(unittest.TestCase):

    def test_plan_creation(self) -> None:
        plan = _standard_plan()
        self.assertEqual(plan.version, "1.0.0")
        self.assertEqual(len(plan.deployment_steps), 5)
        self.assertEqual(len(plan.rollback_plan), 2)

    def test_plan_serialization(self) -> None:
        """BR-052-008: Plan is serializable."""
        d = _standard_plan().to_dict()
        self.assertEqual(d["deployment_id"], "DEPLOY-001")
        self.assertIn("deployment_steps", d)
        self.assertIn("prerequisites", d)

    def test_plan_empty_steps_default(self) -> None:
        plan = DeploymentPlan("DEPLOY-EMPTY", "TESTING", "0.0.1")
        self.assertEqual(plan.deployment_steps, [])
        self.assertEqual(plan.rollback_plan, [])


# ---------------------------------------------------------------------------
# DeploymentReport Tests
# ---------------------------------------------------------------------------

class TestDeploymentReport(unittest.TestCase):

    def _make_report(self, failed: list[str] | None = None, rollback: bool = False) -> DeploymentReport:
        return DeploymentReport(
            deployment_id="DEPLOY-001",
            installed_version="1.0.0",
            target_environment="DEVELOPMENT",
            completed_steps=["install_core", "apply_config"],
            failed_steps=failed or [],
            warnings=[],
            validation_results={"kernel_boot": True},
            execution_time_seconds=1.5,
            rollback_triggered=rollback,
        )

    def test_successful_report_success_flag(self) -> None:
        report = self._make_report()
        self.assertTrue(report.success)

    def test_failed_report_success_flag(self) -> None:
        report = self._make_report(failed=["run_migrations"])
        self.assertFalse(report.success)

    def test_rollback_report_success_flag(self) -> None:
        report = self._make_report(rollback=True)
        self.assertFalse(report.success)

    def test_report_immutability(self) -> None:
        """BR-052-006: DeploymentReport is immutable after creation."""
        report = self._make_report()
        with self.assertRaises(AttributeError):
            report.installed_version = "9.9.9"

    def test_report_serialization(self) -> None:
        """BR-052-008: Report is serializable."""
        d = self._make_report().to_dict()
        self.assertEqual(d["installed_version"], "1.0.0")
        self.assertIn("success", d)
        self.assertIn("completed_steps", d)


# ---------------------------------------------------------------------------
# ConfigProfileManager Tests
# ---------------------------------------------------------------------------

class TestConfigProfileManager(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = ConfigProfileManager()

    def test_dev_profile_uses_mock_ai(self) -> None:
        profile = self.mgr.get_profile("DEVELOPMENT")
        self.assertEqual(profile["ai_provider"], "mock")

    def test_prod_profile_uses_real_ai(self) -> None:
        profile = self.mgr.get_profile("PRODUCTION")
        self.assertEqual(profile["ai_provider"], "openai")

    def test_profiles_are_isolated(self) -> None:
        """BR-052-005: Dev and Prod profiles are independent."""
        dev = self.mgr.get_profile("DEVELOPMENT")
        prod = self.mgr.get_profile("PRODUCTION")
        self.assertNotEqual(dev["logging"], prod["logging"])
        self.assertNotEqual(dev["security"], prod["security"])

    def test_merge_overrides_applied(self) -> None:
        merged = self.mgr.merge_overrides("DEVELOPMENT", {"custom_key": "value"})
        self.assertEqual(merged["custom_key"], "value")
        self.assertEqual(merged["ai_provider"], "mock")

    def test_merge_does_not_mutate_base_profile(self) -> None:
        self.mgr.merge_overrides("DEVELOPMENT", {"ai_provider": "anthropic"})
        original = self.mgr.get_profile("DEVELOPMENT")
        self.assertEqual(original["ai_provider"], "mock")


# ---------------------------------------------------------------------------
# VersionRegistry Tests
# ---------------------------------------------------------------------------

class TestVersionRegistry(unittest.TestCase):

    def test_record_install(self) -> None:
        reg = VersionRegistry()
        reg.record("INSTALL", "1.0.0", "DEVELOPMENT", True)
        self.assertEqual(reg.installed_version, "1.0.0")

    def test_record_upgrade_updates_version(self) -> None:
        reg = VersionRegistry()
        reg.record("INSTALL", "1.0.0", "DEVELOPMENT", True)
        reg.record("UPGRADE", "1.1.0", "PRODUCTION", True)
        self.assertEqual(reg.installed_version, "1.1.0")

    def test_failed_install_does_not_update_version(self) -> None:
        reg = VersionRegistry()
        reg.record("INSTALL", "1.0.0", "DEVELOPMENT", False)
        self.assertIsNone(reg.installed_version)

    def test_history_accumulates(self) -> None:
        reg = VersionRegistry()
        reg.record("INSTALL", "1.0.0", "DEVELOPMENT", True)
        reg.record("ROLLBACK", "previous", "DEVELOPMENT", True)
        self.assertEqual(len(reg.get_history()), 2)

    def test_version_registry_serialization(self) -> None:
        """BR-052-008: VersionRegistry is serializable."""
        reg = VersionRegistry()
        reg.record("INSTALL", "1.0.0", "STAGING", True)
        d = reg.to_dict()
        self.assertEqual(d["installed_version"], "1.0.0")
        self.assertEqual(len(d["history"]), 1)


# ---------------------------------------------------------------------------
# DeploymentManager Integration Tests
# ---------------------------------------------------------------------------

class TestDeploymentManager(unittest.TestCase):

    def setUp(self) -> None:
        self.manager = DeploymentManager()

    def test_successful_deployment(self) -> None:
        """BR-052-001: Deployment is repeatable and succeeds."""
        plan = _standard_plan()
        env = _dev_env()
        report = self.manager.execute_plan(plan, env)
        self.assertTrue(report.success)
        self.assertEqual(env.status, "ACTIVE")
        self.assertEqual(len(report.completed_steps), 5)

    def test_failed_step_triggers_rollback(self) -> None:
        """BR-052-002: Failed step triggers rollback."""
        plan = _standard_plan()
        env = _dev_env()
        report = self.manager.execute_plan(plan, env, fail_on_step="install_core")
        self.assertFalse(report.success)
        self.assertTrue(report.rollback_triggered)
        self.assertIn("install_core", report.failed_steps)
        self.assertEqual(env.status, "FAILED")

    def test_rollback_history_recorded(self) -> None:
        """BR-052-002 + BR-052-007: Rollback recorded but no data lost."""
        plan = _standard_plan()
        env = _dev_env()
        self.manager.execute_plan(plan, env, fail_on_step="run_migrations")
        history = self.manager.version_registry.get_history()
        rollback_events = [h for h in history if h["event_type"] == "ROLLBACK"]
        self.assertEqual(len(rollback_events), 1)

    def test_prerequisite_validation_runs(self) -> None:
        """BR-052-004: Validation executes before steps."""
        env = _dev_env()
        results = self.manager.validate_environment(env)
        self.assertIn("check_python_version", results)
        self.assertTrue(results["check_python_version"])

    def test_health_check_runs_post_deployment(self) -> None:
        """BR-052-009: Health checks run automatically."""
        plan = _standard_plan()
        env = _dev_env()
        report = self.manager.execute_plan(plan, env)
        self.assertIn("kernel_boot", report.validation_results)
        self.assertTrue(report.validation_results["kernel_boot"])

    def test_health_check_fails_on_failed_env(self) -> None:
        env = _dev_env()
        env.status = "FAILED"
        health = self.manager.run_health_check(env)
        self.assertFalse(health["kernel_boot"])

    def test_deployment_report_explainability(self) -> None:
        """BR-052-010: Report carries recommendations and step detail."""
        plan = _standard_plan()
        env = _dev_env()
        report = self.manager.execute_plan(plan, env, fail_on_step="apply_config")
        self.assertTrue(len(report.recommendations) > 0)
        self.assertIn("Investigate failed step", report.recommendations[0])

    def test_version_recorded_on_success(self) -> None:
        plan = _standard_plan()
        env = _dev_env()
        self.manager.execute_plan(plan, env)
        self.assertEqual(self.manager.version_registry.installed_version, "1.0.0")

    def test_upgrade_flow(self) -> None:
        plan_v1 = _standard_plan()
        env = _dev_env()
        self.manager.execute_plan(plan_v1, env)

        plan_v2 = DeploymentPlan("DEPLOY-002", "DEVELOPMENT", "1.1.0",
                                  deployment_steps=["apply_patch", "verify_install"],
                                  rollback_plan=["restore_config"])
        report = self.manager.upgrade(plan_v2, env)
        self.assertTrue(report.success)
        history = self.manager.version_registry.get_history()
        self.assertTrue(any(h["event_type"] == "UPGRADE" for h in history))

    def test_deployment_repeatability(self) -> None:
        """BR-052-001: Same plan can be executed twice cleanly."""
        plan = _standard_plan()
        env1 = _dev_env()
        env2 = DeploymentEnvironment("ENV-002", "TESTING")
        report1 = self.manager.execute_plan(plan, env1)
        report2 = self.manager.execute_plan(plan, env2)
        self.assertTrue(report1.success)
        self.assertTrue(report2.success)


if __name__ == "__main__":
    unittest.main()
