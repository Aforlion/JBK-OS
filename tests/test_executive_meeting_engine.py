import unittest
from datetime import datetime, timezone

from core.project import Project, ProjectStatus
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.chief_of_staff import ChiefOfStaff
from core.executive_meeting import ExecutiveMeeting, AgendaItem, ExecutiveDecision, ExecutiveActionItem
from core.executive_meeting_report import ExecutiveMeetingReport
from core.executive_meeting_engine import ExecutiveMeetingEngine


class TestExecutiveMeetingEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.project_registry = ProjectRegistry()
        self.worker_registry = WorkerRegistry()
        self.knowledge_registry = KnowledgeRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
            knowledge_registry=self.knowledge_registry,
        )

        self.engine = ExecutiveMeetingEngine()

        # Seed registry with an active project to trigger agenda generation
        self.project = self.chief_of_staff.create_project(
            project_id="PROJ-M1",
            title="NIC Client Portal Integration",
            client="NIC Inc",
            description="Active frontend-backend mapping.",
        )
        self.project.update_status(ProjectStatus.ACTIVE, actor="system")
        self.chief_of_staff.register_project(self.project)

        self.participants = ["CEO-John", "CTO-Bob", "CFO-Alice", "COO-Mark"]

        # Default briefings where viewpoints align
        self.aligned_briefings = {
            "CTO": "Engineering team is ready to scale the module.",
            "CFO": "Capital budget allocations are healthy.",
            "COO": "Capacity is ready for next sprint launch.",
        }

        # Conflicting briefings
        self.conflicting_briefings = {
            "CTO": "We need to build our custom Postgres pooling tool internally.",
            "CFO": "We must buy an off-the-shelf postgres licensing product.",
            "COO": "Operations are ready.",
        }

    # ------------------------------------------------------------------
    # Agenda and Meeting Creation (BR-040-001, BR-040-004)
    # ------------------------------------------------------------------

    def test_agenda_and_meeting_creation(self) -> None:
        report = self.engine.conduct_meeting(
            meeting_type="Weekly Executive Review",
            participants=self.participants,
            chief_of_staff=self.chief_of_staff,
            executive_briefings=self.aligned_briefings,
        )

        self.assertIsInstance(report, ExecutiveMeetingReport)
        self.assertTrue(report.meeting_id.startswith("MTG-"))
        self.assertEqual(report.meeting_type, "Weekly Executive Review")
        
        # Verify active projects review was appended to agenda
        titles = {i["title"] for i in report.agenda}
        self.assertIn("Active Projects Status Review", titles)

    # ------------------------------------------------------------------
    # Briefing Collection & Consensus Detection (BR-040-005, BR-040-010)
    # ------------------------------------------------------------------

    def test_briefing_aggregation_and_consensus(self) -> None:
        report = self.engine.conduct_meeting(
            meeting_type="Monthly Strategy Review",
            participants=self.participants,
            chief_of_staff=self.chief_of_staff,
            executive_briefings=self.aligned_briefings,
        )

        self.assertTrue(report.consensus_achieved)
        self.assertEqual(len(report.decisions), 1)
        self.assertEqual(report.decisions[0]["outcome"], "APPROVED")
        self.assertEqual(len(report.action_items), 1)
        self.assertEqual(report.action_items[0]["owner"], "COO")

    # ------------------------------------------------------------------
    # Conflict Detection & CEO Override (BR-040-009, BR-040-011)
    # ------------------------------------------------------------------

    def test_conflict_detection_without_override(self) -> None:
        report = self.engine.conduct_meeting(
            meeting_type="Emergency Executive Session",
            participants=self.participants,
            chief_of_staff=self.chief_of_staff,
            executive_briefings=self.conflicting_briefings,
        )

        self.assertFalse(report.consensus_achieved)
        self.assertEqual(len(report.unresolved_items), 1)
        self.assertIn("CTO recommends 'Build' while CFO recommends 'Buy'", report.unresolved_items[0]["conflict"])
        
        # Decision outcome should be postponed
        self.assertEqual(report.decisions[0]["outcome"], "POSTPONED")

    def test_ceo_override_resolves_conflict(self) -> None:
        # Resolve build/buy choice in favor of CTO
        overrides = {
            "Active Projects Status Review": "Build Internally",
        }

        report = self.engine.conduct_meeting(
            meeting_type="Quarterly Business Review",
            participants=self.participants,
            chief_of_staff=self.chief_of_staff,
            executive_briefings=self.conflicting_briefings,
            ceo_override_decisions=overrides,
        )

        # Consensus should now pass due to CEO Override
        self.assertTrue(report.consensus_achieved)
        self.assertEqual(len(report.unresolved_items), 0)
        self.assertEqual(report.decisions[0]["outcome"], "APPROVED (CEO OVERRIDE: Build Internally)")
        self.assertIn("Resolved via CEO directive", report.decisions[0]["rationale"])

    # ------------------------------------------------------------------
    # Knowledge Capture & Serialization (BR-040-012, BR-040-013)
    # ------------------------------------------------------------------

    def test_knowledge_capture_and_serialization(self) -> None:
        report = self.engine.conduct_meeting(
            meeting_type="Daily Stand-up",
            participants=self.participants,
            chief_of_staff=self.chief_of_staff,
            executive_briefings=self.aligned_briefings,
        )

        # Consensus was met, should capture to registry
        self.assertEqual(len(self.chief_of_staff.knowledge_registry.list_items()), 1)

        d = report.to_dict()
        self.assertEqual(d["meeting_id"], report.meeting_id)
        self.assertEqual(len(d["attendance"]), 4)

        s = report.summary()
        self.assertTrue(s["consensus_achieved"])
        self.assertEqual(s["action_item_count"], 1)


if __name__ == "__main__":
    unittest.main()
