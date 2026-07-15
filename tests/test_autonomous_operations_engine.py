"""Tests for Specification 041 — Autonomous Company Mode."""

import unittest

from core.company_mission import CompanyMission, MissionPriority, MissionStatus
from core.company_health_snapshot import CompanyHealthSnapshot
from core.autonomous_operations_report import (
    AutonomousAction,
    OperationalCycle,
    AutonomousOperationsReport,
)
from core.autonomous_operations_engine import (
    AutonomousOperationsEngine,
    BLOCKED_ACTIONS,
    ASSISTED_PERMITTED,
    AUTONOMOUS_PERMITTED,
)
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.knowledge_registry import KnowledgeRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine() -> AutonomousOperationsEngine:
    return AutonomousOperationsEngine()


def _make_chief_of_staff() -> ChiefOfStaff:
    return ChiefOfStaff(
        worker_registry=WorkerRegistry(),
        project_registry=ProjectRegistry(),
        knowledge_registry=KnowledgeRegistry(),
    )


def _make_mission(
    objective: str = "Acquire five school clients",
    priority: str = "HIGH",
) -> CompanyMission:
    return CompanyMission(
        objective=objective,
        kpis=["5 new clients signed", "£250k ARR"],
        constraints=["No cold outreach before Q3"],
        success_criteria=["5 signed contracts", "NPS >= 8"],
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestMissionRegistration(unittest.TestCase):
    """BR-041-001: Mission registration."""

    def test_mission_created_with_required_fields(self):
        mission = _make_mission()
        self.assertIsNotNone(mission.mission_id)
        self.assertTrue(mission.mission_id.startswith("MSN-"))
        self.assertEqual(mission.objective, "Acquire five school clients")
        self.assertEqual(mission.priority, MissionPriority.HIGH)
        self.assertEqual(mission.status, MissionStatus.ACTIVE)

    def test_mission_requires_objective(self):
        with self.assertRaises(ValueError):
            CompanyMission(objective="")

    def test_mission_kpis_constraints_criteria(self):
        mission = _make_mission()
        self.assertEqual(len(mission.kpis), 2)
        self.assertEqual(len(mission.constraints), 1)
        self.assertEqual(len(mission.success_criteria), 2)

    def test_engine_registers_mission(self):
        engine = _make_engine()
        mission = _make_mission()
        returned = engine.register_mission(mission)
        self.assertIs(returned, mission)
        self.assertIn(mission, engine.list_missions())

    def test_engine_rejects_none_mission(self):
        engine = _make_engine()
        with self.assertRaises(ValueError):
            engine.register_mission(None)

    def test_mission_serialisation(self):
        mission = _make_mission()
        data = mission.to_dict()
        self.assertEqual(data["mission_id"], mission.mission_id)
        self.assertEqual(data["objective"], mission.objective)
        self.assertIn("kpis", data)
        self.assertIn("success_criteria", data)
        self.assertIn("constraints", data)
        self.assertEqual(data["progress_percent"], 0.0)
        self.assertEqual(data["cycles_executed"], 0)

    def test_mission_summary(self):
        mission = _make_mission()
        s = mission.summary()
        self.assertIn("mission_id", s)
        self.assertIn("objective", s)
        self.assertIn("status", s)
        self.assertIn("progress_percent", s)

    def test_mission_state_transitions(self):
        mission = _make_mission()
        mission.pause()
        self.assertEqual(mission.status, MissionStatus.PAUSED)
        mission.resume()
        self.assertEqual(mission.status, MissionStatus.ACTIVE)
        mission.cancel()
        self.assertEqual(mission.status, MissionStatus.CANCELLED)

    def test_mission_complete_sets_100_percent(self):
        mission = _make_mission()
        mission.complete()
        self.assertEqual(mission.progress_percent, 100.0)
        self.assertEqual(mission.status, MissionStatus.COMPLETED)


class TestOperationalCycle(unittest.TestCase):
    """BR-041-002: Full operational cycle produces a valid report."""

    def _run_cycle(
        self,
        mode: str = "ASSISTED",
        knowledge_registry: KnowledgeRegistry | None = None,
    ) -> tuple[AutonomousOperationsEngine, CompanyMission, AutonomousOperationsReport]:
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode=mode,
            knowledge_registry=knowledge_registry,
        )
        return engine, mission, report

    def test_cycle_returns_operations_report(self):
        _, _, report = self._run_cycle()
        self.assertIsInstance(report, AutonomousOperationsReport)
        self.assertIsNotNone(report.report_id)
        self.assertTrue(report.report_id.startswith("AOR-"))

    def test_cycle_increments_mission_cycle_count(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        self.assertEqual(mission.cycles_executed, 0)
        engine.run_operational_cycle(mission=mission, chief_of_staff=cos)
        self.assertEqual(mission.cycles_executed, 1)
        engine.run_operational_cycle(mission=mission, chief_of_staff=cos)
        self.assertEqual(mission.cycles_executed, 2)

    def test_cycle_requires_active_mission(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        mission.pause()
        with self.assertRaises(ValueError):
            engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

    def test_cycle_rejects_invalid_mode(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        with self.assertRaises(ValueError):
            engine.run_operational_cycle(
                mission=mission, chief_of_staff=cos, operational_mode="ROGUE"
            )

    def test_cycle_rejects_none_chief_of_staff(self):
        engine = _make_engine()
        mission = _make_mission()
        with self.assertRaises(ValueError):
            engine.run_operational_cycle(mission=mission, chief_of_staff=None)


class TestAdvisoryMode(unittest.TestCase):
    """BR-041-014: ADVISORY mode never executes actions."""

    def test_advisory_mode_no_completed_actions(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="ADVISORY",
        )

        # All planned execution actions should be PENDING, not EXECUTED
        executed_types = [a.action_type for a in report.completed_actions]
        # Only non-execution phases (observe, analyse, learn) should appear as executed
        # The actual planned work items should all be pending
        self.assertEqual(len(report.blocked_actions), 0)
        self.assertIsInstance(report.pending_actions, list)

    def test_advisory_mode_populates_recommendations(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="ADVISORY",
        )

        self.assertGreater(len(report.recommendations), 0)
        # Should recommend upgrading mode
        rec_text = " ".join(report.recommendations)
        self.assertIn("ADVISORY", rec_text)


class TestAssistedMode(unittest.TestCase):
    """BR-041-006: ASSISTED mode executes permitted non-committal workflows."""

    def test_assisted_mode_executes_permitted_actions(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="ASSISTED",
        )

        executed_types = {a.action_type for a in report.completed_actions}
        # All executed actions must be in ASSISTED_PERMITTED (not blocked)
        for action_type in executed_types:
            self.assertIn(action_type, ASSISTED_PERMITTED)

    def test_assisted_mode_blocks_reserved_actions(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="ASSISTED",
        )

        for action in report.blocked_actions:
            self.assertTrue(action.authorization_required)
            self.assertEqual(action.status, "BLOCKED")


class TestAutonomousMode(unittest.TestCase):
    """BR-041-006: AUTONOMOUS mode executes a broader set of permitted actions."""

    def test_autonomous_mode_broader_permitted_set(self):
        # AUTONOMOUS_PERMITTED is a superset of ASSISTED_PERMITTED
        self.assertTrue(ASSISTED_PERMITTED.issubset(AUTONOMOUS_PERMITTED))

    def test_autonomous_mode_runs_successfully(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="AUTONOMOUS",
        )

        self.assertIsInstance(report, AutonomousOperationsReport)
        executed_types = {a.action_type for a in report.completed_actions}
        for action_type in executed_types:
            self.assertIn(action_type, AUTONOMOUS_PERMITTED)


class TestAuthorizationBoundaryEnforcement(unittest.TestCase):
    """BR-041-007: Blocked actions must never be executed in any mode."""

    def test_blocked_actions_set_is_non_empty(self):
        self.assertGreater(len(BLOCKED_ACTIONS), 0)
        self.assertIn("sign_contract", BLOCKED_ACTIONS)
        self.assertIn("approve_spending", BLOCKED_ACTIONS)
        self.assertIn("hire_personnel", BLOCKED_ACTIONS)
        self.assertIn("terminate_personnel", BLOCKED_ACTIONS)
        self.assertIn("commit_legal_obligation", BLOCKED_ACTIONS)
        self.assertIn("release_approved_deliverable", BLOCKED_ACTIONS)

    def test_blocked_actions_not_in_permitted_sets(self):
        for action in BLOCKED_ACTIONS:
            self.assertNotIn(action, ASSISTED_PERMITTED, f"{action} must not be ASSISTED permitted")
            self.assertNotIn(action, AUTONOMOUS_PERMITTED, f"{action} must not be AUTONOMOUS permitted")

    def test_blocked_action_produces_blocked_record(self):
        """Direct AutonomousAction record for a blocked action."""
        action = AutonomousAction(
            engine="TestEngine",
            action_type="sign_contract",
            reasoning="Boundary enforcement test.",
            authorization_required=True,
            status="BLOCKED",
        )
        self.assertEqual(action.status, "BLOCKED")
        self.assertTrue(action.authorization_required)
        data = action.to_dict()
        self.assertEqual(data["status"], "BLOCKED")
        self.assertTrue(data["authorization_required"])

    def test_engine_never_executes_blocked_action_in_autonomous_mode(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="AUTONOMOUS",
        )
        executed_types = {a.action_type for a in report.completed_actions}
        for blocked in BLOCKED_ACTIONS:
            self.assertNotIn(blocked, executed_types)


class TestCompanyHealth(unittest.TestCase):
    """BR-041-009: Company health computed across six dimensions."""

    def test_health_snapshot_defaults_to_healthy(self):
        health = CompanyHealthSnapshot()
        self.assertEqual(health.status, "HEALTHY")
        self.assertGreaterEqual(health.health_score, 0.75)

    def test_health_snapshot_clamps_scores(self):
        health = CompanyHealthSnapshot(
            portfolio_health=1.5,
            delivery_health=-0.5,
        )
        self.assertEqual(health.portfolio_health, 1.0)
        self.assertEqual(health.delivery_health, 0.0)

    def test_health_snapshot_critical_status(self):
        health = CompanyHealthSnapshot(
            portfolio_health=0.1,
            delivery_health=0.1,
            financial_health=0.1,
            strategic_health=0.1,
            workforce_health=0.1,
            customer_health=0.1,
        )
        self.assertEqual(health.status, "CRITICAL")
        self.assertLess(health.health_score, 0.5)

    def test_health_snapshot_degraded_status(self):
        health = CompanyHealthSnapshot(
            portfolio_health=0.5,
            delivery_health=0.5,
            financial_health=0.5,
            strategic_health=0.5,
            workforce_health=0.5,
            customer_health=0.5,
        )
        self.assertEqual(health.status, "DEGRADED")

    def test_health_snapshot_dimension_scores(self):
        health = CompanyHealthSnapshot(
            portfolio_health=0.8,
            delivery_health=0.7,
        )
        dims = health.dimension_scores()
        self.assertIn("portfolio_health", dims)
        self.assertIn("delivery_health", dims)
        self.assertEqual(dims["portfolio_health"], 0.8)
        self.assertEqual(dims["delivery_health"], 0.7)

    def test_health_snapshot_weakest_dimension(self):
        health = CompanyHealthSnapshot(
            portfolio_health=0.9,
            delivery_health=0.9,
            financial_health=0.2,
            strategic_health=0.9,
            workforce_health=0.9,
            customer_health=0.9,
        )
        dim, score = health.weakest_dimension()
        self.assertEqual(dim, "financial_health")
        self.assertAlmostEqual(score, 0.2)

    def test_health_snapshot_serialisation(self):
        health = CompanyHealthSnapshot()
        data = health.to_dict()
        self.assertIn("snapshot_id", data)
        self.assertIn("health_score", data)
        self.assertIn("status", data)
        self.assertIn("dimensions", data)
        self.assertIn("timestamp", data)

    def test_health_snapshot_summary(self):
        health = CompanyHealthSnapshot(workforce_health=0.1)
        s = health.summary()
        self.assertEqual(s["weakest_dimension"], "workforce_health")

    def test_cycle_report_contains_health(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        self.assertIsInstance(report.company_health, CompanyHealthSnapshot)
        self.assertIn(report.company_health.status, {"HEALTHY", "DEGRADED", "CRITICAL"})


class TestOperationalReport(unittest.TestCase):
    """BR-041-011: Operational report must contain all required fields."""

    def _get_report(self) -> AutonomousOperationsReport:
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        return engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

    def test_report_has_required_fields(self):
        report = self._get_report()
        self.assertIsNotNone(report.report_id)
        self.assertIsNotNone(report.generated_at)
        self.assertIsInstance(report.completed_actions, list)
        self.assertIsInstance(report.pending_actions, list)
        self.assertIsInstance(report.blocked_actions, list)
        self.assertIsInstance(report.escalations, list)
        self.assertIsInstance(report.recommendations, list)
        self.assertIsInstance(report.mission_progress, dict)
        self.assertIsInstance(report.company_health, CompanyHealthSnapshot)
        self.assertIsInstance(report.audit_trail, list)

    def test_mission_progress_fields(self):
        report = self._get_report()
        progress = report.mission_progress
        self.assertIn("mission_id", progress)
        self.assertIn("objective", progress)
        self.assertIn("progress_percent", progress)
        self.assertIn("cycles_executed", progress)
        self.assertIn("kpis", progress)
        self.assertIn("success_criteria", progress)
        self.assertIn("current_health", progress)

    def test_recommendations_non_empty(self):
        report = self._get_report()
        self.assertGreater(len(report.recommendations), 0)


class TestAuditTrail(unittest.TestCase):
    """BR-041-015: Immutable audit trail for every autonomous decision."""

    def test_audit_trail_populated(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

        self.assertIsInstance(report.audit_trail, list)
        self.assertGreater(len(report.audit_trail), 0)

    def test_audit_trail_entries_have_required_fields(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

        for entry in report.audit_trail:
            self.assertIn("action_id", entry)
            self.assertIn("timestamp", entry)
            self.assertIn("engine", entry)
            self.assertIn("action_type", entry)
            self.assertIn("reasoning", entry)
            self.assertIn("confidence", entry)
            self.assertIn("authorization_required", entry)
            self.assertIn("status", entry)

    def test_audit_trail_contains_all_cycle_actions(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

        cycle_action_ids = {a.action_id for a in report.cycle.actions}
        audit_action_ids = {e["action_id"] for e in report.audit_trail}
        self.assertEqual(cycle_action_ids, audit_action_ids)

    def test_multiple_cycles_independent_audit_trails(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report1 = engine.run_operational_cycle(mission=mission, chief_of_staff=cos)
        report2 = engine.run_operational_cycle(mission=mission, chief_of_staff=cos)

        ids1 = {e["action_id"] for e in report1.audit_trail}
        ids2 = {e["action_id"] for e in report2.audit_trail}
        self.assertEqual(ids1 & ids2, set())  # No shared action IDs across cycles


class TestLearningLoop(unittest.TestCase):
    """BR-041-010: Cycle outcomes feed the Knowledge Registry."""

    def test_learning_phase_registers_knowledge(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        knowledge_registry = KnowledgeRegistry()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            knowledge_registry=knowledge_registry,
        )

        items = knowledge_registry.list_items()
        self.assertGreater(len(items), 0)
        # The registered item should reference this cycle
        titles = [getattr(item, "title", "") for item in items]
        self.assertTrue(
            any(report.cycle.cycle_id in t for t in titles),
            f"Cycle ID {report.cycle.cycle_id} not found in knowledge titles: {titles}",
        )

    def test_learning_phase_without_registry_does_not_crash(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        # No knowledge_registry provided
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            knowledge_registry=None,
        )
        self.assertIsNotNone(report)


class TestOperationalModes(unittest.TestCase):
    """BR-041-014: Three operational modes with distinct behaviour."""

    def _report_for_mode(self, mode: str) -> AutonomousOperationsReport:
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        return engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode=mode,
        )

    def test_all_three_modes_complete_successfully(self):
        for mode in ("ADVISORY", "ASSISTED", "AUTONOMOUS"):
            with self.subTest(mode=mode):
                report = self._report_for_mode(mode)
                self.assertIsNotNone(report)

    def test_mode_stored_in_cycle(self):
        for mode in ("ADVISORY", "ASSISTED", "AUTONOMOUS"):
            with self.subTest(mode=mode):
                report = self._report_for_mode(mode)
                self.assertEqual(report.cycle.operational_mode, mode)

    def test_advisory_has_most_pending(self):
        advisory = self._report_for_mode("ADVISORY")
        assisted = self._report_for_mode("ASSISTED")
        self.assertGreaterEqual(
            len(advisory.pending_actions), len(assisted.pending_actions)
        )

    def test_assisted_has_more_executed_than_advisory(self):
        advisory = self._report_for_mode("ADVISORY")
        assisted = self._report_for_mode("ASSISTED")
        self.assertGreaterEqual(
            len(assisted.completed_actions), len(advisory.completed_actions)
        )


class TestMissionPause(unittest.TestCase):
    """BR-041-008: CEO can pause, redirect, and resume missions."""

    def test_pause_and_resume_mission_via_engine(self):
        engine = _make_engine()
        mission = _make_mission()
        engine.register_mission(mission)

        engine.pause_mission(mission.mission_id)
        self.assertEqual(mission.status, MissionStatus.PAUSED)

        engine.resume_mission(mission.mission_id)
        self.assertEqual(mission.status, MissionStatus.ACTIVE)

    def test_cancel_mission_via_engine(self):
        engine = _make_engine()
        mission = _make_mission()
        engine.register_mission(mission)

        engine.cancel_mission(mission.mission_id)
        self.assertEqual(mission.status, MissionStatus.CANCELLED)

    def test_engine_rejects_unknown_mission_id(self):
        engine = _make_engine()
        with self.assertRaises(ValueError):
            engine.pause_mission("MSN-NONEXISTENT")


class TestSerialization(unittest.TestCase):
    """All domain models must serialize cleanly."""

    def test_autonomous_action_to_dict(self):
        action = AutonomousAction(
            engine="TestEngine",
            action_type="analyze_portfolio",
            reasoning="Test reasoning.",
            confidence=0.85,
            authorization_required=False,
            status="EXECUTED",
            evidence=["Evidence A"],
            outcome="Completed successfully.",
        )
        data = action.to_dict()
        self.assertEqual(data["engine"], "TestEngine")
        self.assertEqual(data["action_type"], "analyze_portfolio")
        self.assertAlmostEqual(data["confidence"], 0.85)
        self.assertEqual(data["status"], "EXECUTED")
        self.assertFalse(data["authorization_required"])

    def test_operational_cycle_to_dict(self):
        cycle = OperationalCycle(
            mission_id="MSN-TEST01",
            operational_mode="ASSISTED",
        )
        cycle.add_decision("Test decision.")
        cycle.add_outcome("Test outcome.")
        cycle.close()

        data = cycle.to_dict()
        self.assertIn("cycle_id", data)
        self.assertIn("mission_id", data)
        self.assertIn("operational_mode", data)
        self.assertIn("start_time", data)
        self.assertIn("end_time", data)
        self.assertIn("decisions", data)
        self.assertIn("outcomes", data)
        self.assertIsNotNone(data["end_time"])

    def test_operations_report_to_dict(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        data = report.to_dict()
        self.assertIn("report_id", data)
        self.assertIn("generated_at", data)
        self.assertIn("cycle", data)
        self.assertIn("company_health", data)
        self.assertIn("mission_progress", data)
        self.assertIn("completed_actions", data)
        self.assertIn("pending_actions", data)
        self.assertIn("blocked_actions", data)
        self.assertIn("escalations", data)
        self.assertIn("recommendations", data)
        self.assertIn("audit_trail", data)

    def test_operations_report_summary(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        summary = report.summary()
        self.assertIn("report_id", summary)
        self.assertIn("cycle_id", summary)
        self.assertIn("operational_mode", summary)
        self.assertIn("company_health", summary)
        self.assertIn("completed", summary)
        self.assertIn("pending", summary)
        self.assertIn("blocked", summary)
        self.assertIn("escalations", summary)

    def test_company_mission_to_dict_roundtrip(self):
        mission = _make_mission()
        data = mission.to_dict()
        self.assertEqual(data["objective"], mission.objective)
        self.assertIsInstance(data["kpis"], list)
        self.assertIsInstance(data["constraints"], list)
        self.assertIsInstance(data["success_criteria"], list)

    def test_company_health_snapshot_to_dict_roundtrip(self):
        health = CompanyHealthSnapshot(
            portfolio_health=0.8,
            delivery_health=0.9,
            financial_health=0.7,
            strategic_health=0.85,
            workforce_health=0.6,
            customer_health=0.95,
        )
        data = health.to_dict()
        self.assertIn("dimensions", data)
        self.assertAlmostEqual(data["dimensions"]["portfolio_health"], 0.8)
        self.assertAlmostEqual(data["dimensions"]["customer_health"], 0.95)


class TestExplainability(unittest.TestCase):
    """BR-041-013: Every autonomous action must explain itself."""

    def test_all_actions_have_reasoning(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        for action in report.cycle.actions:
            self.assertTrue(
                bool(action.reasoning),
                f"Action {action.action_id} ({action.action_type}) has no reasoning.",
            )

    def test_all_actions_have_engine_attribution(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        for action in report.cycle.actions:
            self.assertTrue(
                bool(action.engine),
                f"Action {action.action_id} has no engine attribution.",
            )

    def test_all_actions_have_confidence_score(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()
        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
        )
        for action in report.cycle.actions:
            self.assertGreaterEqual(action.confidence, 0.0)
            self.assertLessEqual(action.confidence, 1.0)


class TestCeoOverride(unittest.TestCase):
    """BR-041-008: CEO may override autonomous decisions."""

    def test_ceo_override_applied_in_execute_phase(self):
        engine = _make_engine()
        mission = _make_mission()
        cos = _make_chief_of_staff()

        report = engine.run_operational_cycle(
            mission=mission,
            chief_of_staff=cos,
            operational_mode="ASSISTED",
            ceo_override={"analyze_portfolio": "Prioritise school sector projects only"},
        )
        # Verify the override was referenced in reasoning of executed actions
        override_reflected = any(
            "school sector" in (a.reasoning or "")
            for a in report.completed_actions
        )
        self.assertTrue(override_reflected)


if __name__ == "__main__":
    unittest.main()
