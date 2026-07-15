import unittest

from core.project import Project, ProjectStatus
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.deliverable import Deliverable, DeliverableStatus
from core.delivery_status_report import DeliveryStatusReport
from core.execution_report import ExecutionReport
from core.solution_blueprint import SolutionBlueprint
from core.organizational_knowledge import (
    KnowledgeCategory,
    KnowledgeConfidence,
    LessonLearned,
    BestPractice,
    ReusableAsset,
    ProjectPattern,
    OrganizationalKnowledge,
)
from core.organizational_memory_report import OrganizationalMemoryReport
from core.organizational_memory_engine import OrganizationalMemoryEngine


def _make_completed_project(project_id: str = "PROJ-0001") -> Project:
    p = Project(
        title="School Management System",
        client="Ministry of Education",
        description="Build a full school management platform.",
        project_id=project_id,
        status=ProjectStatus.COMPLETED,
    )
    return p


def _make_chief_of_staff(knowledge_registry: KnowledgeRegistry | None = None) -> ChiefOfStaff:
    return ChiefOfStaff(
        worker_registry=WorkerRegistry(),
        project_registry=ProjectRegistry(),
        knowledge_registry=knowledge_registry or KnowledgeRegistry(),
    )


def _make_delivery_report(health: str = "HEALTHY") -> DeliveryStatusReport:
    return DeliveryStatusReport(
        report_id="SUP-0001",
        project_id="PROJ-0001",
        health_status=health,
        active_work=[],
        waiting_work=[],
        completed_work=[{"work_order_id": "WO-0001", "title": "Setup", "status": "COMPLETED"}],
        failed_work=[],
        risk_register=[{"risk": "API latency", "severity": "LOW"}],
        worker_utilization={},
        blockers=[],
        ceo_attention_items=[],
        corrective_recommendations=[],
    )


def _make_execution_report(status: str = "SUCCESS") -> ExecutionReport:
    return ExecutionReport(
        report_id="EXR-0001",
        work_order_id="WO-0001",
        engine_name="Antigravity",
        worker_id="EXEC-0001",
        status=status,
        duration_seconds=42.5,
        outputs={"result": "done"},
        errors=[],
    )


def _make_blueprint() -> SolutionBlueprint:
    return SolutionBlueprint(
        blueprint_id="BP-001",
        opportunity_id=None,
        discovery_plan_id="DP-001",
        client_summary="Ministry of Education needs a SOFTWARE platform.",
        business_problem="Manual record management is inefficient.",
        root_cause_analysis={"cause": "paper-based"},
        business_objectives=["Digitize records", "Automate reporting"],
        proposed_solution_options=[{"title": "SaaS Platform"}, {"title": "On-Prem"}],
        recommended_solution={"title": "SaaS Platform", "approach": "Cloud-first"},
        business_benefits=["Efficiency", "Cost reduction"],
        technical_considerations=["Scalability", "GDPR"],
        required_capabilities=["frontend", "backend", "database"],
        required_skills=["Python", "React"],
        required_departments=["Engineering", "QA"],
        estimated_complexity="High",
        risks=["Scope creep", "Data migration risk"],
        assumptions=["Internet available"],
        dependencies=["Existing MIS data"],
        success_metrics=["Zero paper-based records by Q4", "99.9% uptime"],
        executive_recommendation="Proceed with SaaS-first delivery.",
        confidence_score=0.85,
    )


class TestOrganizationalMemoryEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = OrganizationalMemoryEngine()
        self.knowledge_registry = KnowledgeRegistry()
        self.cos = _make_chief_of_staff(self.knowledge_registry)

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    def test_rejects_none_project(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.archive_project(None, self.cos)  # type: ignore

    def test_rejects_none_chief_of_staff(self) -> None:
        project = _make_completed_project()
        with self.assertRaises(ValueError):
            self.engine.archive_project(project, None)  # type: ignore

    def test_rejects_incomplete_project(self) -> None:
        project = Project(
            title="Incomplete Proj",
            client="Client A",
            description="desc",
            project_id="PROJ-9999",
        )
        # status defaults to PLANNED
        with self.assertRaises(ValueError, msg="Should reject non-COMPLETED project"):
            self.engine.archive_project(project, self.cos)

    def test_rejects_active_project(self) -> None:
        project = Project(
            title="Active Proj",
            client="Client B",
            description="desc",
            project_id="PROJ-9998",
            status=ProjectStatus.ACTIVE,
        )
        with self.assertRaises(ValueError):
            self.engine.archive_project(project, self.cos)

    def test_raises_without_knowledge_registry_on_cos(self) -> None:
        cos_no_registry = ChiefOfStaff(
            worker_registry=WorkerRegistry(),
            project_registry=ProjectRegistry(),
        )
        project = _make_completed_project("PROJ-X001")
        with self.assertRaises(ValueError):
            self.engine.archive_project(project, cos_no_registry)

    # ------------------------------------------------------------------
    # Minimal Archival
    # ------------------------------------------------------------------

    def test_minimal_archive_returns_report(self) -> None:
        project = _make_completed_project("PROJ-M001")
        report = self.engine.archive_project(project, self.cos)
        self.assertIsInstance(report, OrganizationalMemoryReport)
        self.assertEqual(report.project_id, "PROJ-M001")

    def test_knowledge_asset_id_format(self) -> None:
        project = _make_completed_project("PROJ-M002")
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertTrue(ka.knowledge_id.startswith("KN-"), f"Expected KN- prefix, got {ka.knowledge_id}")
        self.assertEqual(len(ka.knowledge_id), 9, "KN-000001 should have 9 chars")

    def test_source_project_reference(self) -> None:
        project = _make_completed_project("PROJ-M003")
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertIn("PROJ-M003", ka.source_project_ids)

    def test_knowledge_registered_in_registry(self) -> None:
        project = _make_completed_project("PROJ-M004")
        report = self.engine.archive_project(project, self.cos)
        ka_id = report.knowledge_assets[0].knowledge_id
        stored = self.knowledge_registry.find_by_id(ka_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.knowledge_id, ka_id)

    def test_warnings_on_no_optional_inputs(self) -> None:
        project = _make_completed_project("PROJ-W001")
        report = self.engine.archive_project(project, self.cos)
        # Should warn about missing delivery report, execution reports, blueprint, CEO notes
        self.assertGreater(len(report.warnings), 0)

    # ------------------------------------------------------------------
    # Lessons Learned
    # ------------------------------------------------------------------

    def test_lessons_extracted_from_delivery_blockers(self) -> None:
        project = _make_completed_project("PROJ-L001")
        dr = DeliveryStatusReport(
            report_id="SUP-L001", project_id="PROJ-L001", health_status="AT_RISK",
            active_work=[], waiting_work=[], completed_work=[], failed_work=[],
            risk_register=[],
            worker_utilization={},
            blockers=[{"work_order_id": "WO-0001", "type": "WAIT_LOCK", "description": "Dep not done."}],
            ceo_attention_items=[], corrective_recommendations=[],
        )
        report = self.engine.archive_project(project, self.cos, delivery_report=dr)
        ka = report.knowledge_assets[0]
        self.assertGreater(len(ka.lessons_learned), 0)

    def test_lessons_extracted_from_risk_register(self) -> None:
        project = _make_completed_project("PROJ-L002")
        dr = _make_delivery_report("WATCH")
        report = self.engine.archive_project(project, self.cos, delivery_report=dr)
        ka = report.knowledge_assets[0]
        self.assertGreater(len(ka.lessons_learned), 0)
        titles = [ll.title for ll in ka.lessons_learned]
        self.assertTrue(any("Risk" in t for t in titles))

    def test_lessons_extracted_from_failed_work_orders(self) -> None:
        project = _make_completed_project("PROJ-L003")
        from core.work_order import WorkOrder
        wo = WorkOrder(project_id="PROJ-L003", title="Deploy Prod", objective="deploy")
        wo.status = "FAILED"
        project.work_orders.append(wo)
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertGreater(len(ka.lessons_learned), 0)

    def test_duplicate_lesson_merging(self) -> None:
        """Lessons with same title should merge, not duplicate."""
        project = _make_completed_project("PROJ-L004")
        dr = DeliveryStatusReport(
            report_id="SUP-L004", project_id="PROJ-L004", health_status="AT_RISK",
            active_work=[], waiting_work=[], completed_work=[], failed_work=[],
            risk_register=[],
            worker_utilization={},
            blockers=[
                {"work_order_id": "WO-0001", "type": "WAIT_LOCK", "description": "Same issue."},
                {"work_order_id": "WO-0002", "type": "WAIT_LOCK", "description": "Same issue."},
            ],
            ceo_attention_items=[], corrective_recommendations=[],
        )
        report = self.engine.archive_project(project, self.cos, delivery_report=dr)
        ka = report.knowledge_assets[0]
        # Both blockers have same type so they should merge into one lesson
        blocker_lessons = [ll for ll in ka.lessons_learned if "WAIT_LOCK" in ll.title]
        self.assertEqual(len(blocker_lessons), 1)

    # ------------------------------------------------------------------
    # Best Practices
    # ------------------------------------------------------------------

    def test_best_practices_from_successful_execution_reports(self) -> None:
        project = _make_completed_project("PROJ-B001")
        er = _make_execution_report("SUCCESS")
        report = self.engine.archive_project(project, self.cos, execution_reports=[er])
        ka = report.knowledge_assets[0]
        self.assertGreater(len(ka.best_practices), 0)
        titles = [bp.title for bp in ka.best_practices]
        self.assertTrue(any("Antigravity" in t for t in titles))

    def test_best_practices_from_approved_deliverables(self) -> None:
        project = _make_completed_project("PROJ-B002")
        d = Deliverable(
            project_id="PROJ-B002",
            work_order_id="WO-0001",
            title="Final Report",
            author="EXEC-0001",
            content="Report content",
        )
        d.status = DeliverableStatus.APPROVED
        project.deliverables.append(d)
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        practice_titles = [bp.title for bp in ka.best_practices]
        self.assertTrue(any("Deliverable" in t for t in practice_titles))

    def test_no_best_practices_from_failed_execution(self) -> None:
        project = _make_completed_project("PROJ-B003")
        er = _make_execution_report("FAILED")
        report = self.engine.archive_project(project, self.cos, execution_reports=[er])
        ka = report.knowledge_assets[0]
        # No "Successful Execution" practice expected from a failed run
        titles = [bp.title for bp in ka.best_practices]
        self.assertFalse(any("Successful Execution" in t for t in titles))

    # ------------------------------------------------------------------
    # Reusable Assets
    # ------------------------------------------------------------------

    def test_reusable_assets_from_blueprint(self) -> None:
        project = _make_completed_project("PROJ-A001")
        bp = _make_blueprint()
        report = self.engine.archive_project(project, self.cos, blueprint=bp)
        ka = report.knowledge_assets[0]
        self.assertGreater(len(ka.reusable_assets), 0)
        types = [ra.asset_type for ra in ka.reusable_assets]
        self.assertIn("ARCHITECTURE", types)
        self.assertIn("CHECKLIST", types)

    def test_reusable_assets_from_approved_deliverables(self) -> None:
        project = _make_completed_project("PROJ-A002")
        d = Deliverable(
            project_id="PROJ-A002",
            work_order_id="WO-0001",
            title="Implementation Guide",
            author="EXEC-0001",
            content={"steps": ["step1", "step2"]},
        )
        d.status = DeliverableStatus.APPROVED
        project.deliverables.append(d)
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        types = [ra.asset_type for ra in ka.reusable_assets]
        self.assertIn("TEMPLATE", types)

    # ------------------------------------------------------------------
    # Category and Confidence
    # ------------------------------------------------------------------

    def test_category_derived_from_blueprint(self) -> None:
        project = _make_completed_project("PROJ-C001")
        bp = _make_blueprint()  # client_summary: "Ministry of Education needs a SOFTWARE platform."
        report = self.engine.archive_project(project, self.cos, blueprint=bp)
        ka = report.knowledge_assets[0]
        # The resolver scans enum members in definition order; EDUCATION appears before SOFTWARE
        # in the enum and is present in the blueprint text → EDUCATION is the resolved category.
        self.assertNotEqual(ka.category, KnowledgeCategory.GENERAL)

    def test_category_defaults_to_general_without_blueprint(self) -> None:
        project = _make_completed_project("PROJ-C002")
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertEqual(ka.category, KnowledgeCategory.GENERAL)

    def test_confidence_proven_on_healthy_delivery(self) -> None:
        project = _make_completed_project("PROJ-CF001")
        dr = _make_delivery_report("HEALTHY")
        report = self.engine.archive_project(project, self.cos, delivery_report=dr)
        ka = report.knowledge_assets[0]
        for ll in ka.lessons_learned:
            self.assertIn(ll.confidence, (KnowledgeConfidence.PROVEN, KnowledgeConfidence.EXPERIMENTAL))

    def test_confidence_experimental_without_any_reports(self) -> None:
        project = _make_completed_project("PROJ-CF002")
        report = self.engine.archive_project(project, self.cos)
        # No delivery or execution reports → EXPERIMENTAL confidence used as baseline
        ka = report.knowledge_assets[0]
        for bp in ka.best_practices:
            self.assertEqual(bp.confidence, KnowledgeConfidence.EXPERIMENTAL)

    # ------------------------------------------------------------------
    # Future Recommendations and CEO Notes
    # ------------------------------------------------------------------

    def test_ceo_notes_in_future_recommendations(self) -> None:
        project = _make_completed_project("PROJ-N001")
        notes = ["Always involve IT from Day 1.", "Client prefers weekly demos."]
        report = self.engine.archive_project(project, self.cos, ceo_notes=notes)
        self.assertTrue(any("Always involve IT" in r for r in report.future_recommendations))
        self.assertTrue(any("weekly demos" in r for r in report.future_recommendations))

    def test_blueprint_risks_in_future_recommendations(self) -> None:
        project = _make_completed_project("PROJ-N002")
        bp = _make_blueprint()  # has "Scope creep" and "Data migration risk"
        report = self.engine.archive_project(project, self.cos, blueprint=bp)
        self.assertTrue(any("Scope creep" in r for r in report.future_recommendations))

    # ------------------------------------------------------------------
    # Project Pattern
    # ------------------------------------------------------------------

    def test_project_pattern_extracted(self) -> None:
        project = _make_completed_project("PROJ-PT001")
        from core.work_order import WorkOrder
        wo1 = WorkOrder(project_id="PROJ-PT001", title="Setup Environment", objective="init")
        wo2 = WorkOrder(project_id="PROJ-PT001", title="Deploy Backend", objective="deploy")
        project.work_orders.extend([wo1, wo2])
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertEqual(len(ka.patterns), 1)
        pattern = ka.patterns[0]
        self.assertIsInstance(pattern, ProjectPattern)
        self.assertTrue(pattern.pattern_id.startswith("PT-"))

    # ------------------------------------------------------------------
    # Case Study
    # ------------------------------------------------------------------

    def test_case_study_present(self) -> None:
        project = _make_completed_project("PROJ-CS001")
        report = self.engine.archive_project(project, self.cos)
        self.assertIn("client", report.case_study)
        self.assertIn("outcome", report.case_study)
        self.assertIn("delivery_rate_pct", report.case_study)
        self.assertEqual(report.case_study["client"], "Ministry of Education")

    # ------------------------------------------------------------------
    # Immutability (BR-030-002, BR-030-008)
    # ------------------------------------------------------------------

    def test_project_not_mutated(self) -> None:
        project = _make_completed_project("PROJ-IM001")
        original_title = project.title
        original_client = project.client
        original_description = project.description
        original_status = project.status
        self.engine.archive_project(project, self.cos)
        self.assertEqual(project.title, original_title)
        self.assertEqual(project.client, original_client)
        self.assertEqual(project.description, original_description)
        self.assertEqual(project.status, original_status)

    # ------------------------------------------------------------------
    # Search (BR-030-009)
    # ------------------------------------------------------------------

    def test_knowledge_asset_matches_by_title(self) -> None:
        project = _make_completed_project("PROJ-S001")
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        self.assertTrue(ka.matches("School"))
        self.assertFalse(ka.matches("unicorn_xyz_no_match"))

    def test_knowledge_registry_search(self) -> None:
        project = _make_completed_project("PROJ-S002")
        self.engine.archive_project(project, self.cos)
        results = self.knowledge_registry.search("Ministry")
        self.assertGreater(len(results), 0)

    # ------------------------------------------------------------------
    # Serialization (BR-030-010)
    # ------------------------------------------------------------------

    def test_report_serialization(self) -> None:
        project = _make_completed_project("PROJ-SER001")
        report = self.engine.archive_project(project, self.cos)
        d = report.to_dict()
        self.assertEqual(d["report_id"], report.report_id)
        self.assertIn("knowledge_assets", d)
        self.assertIn("summary", d)

    def test_knowledge_object_serialization(self) -> None:
        project = _make_completed_project("PROJ-SER002")
        bp = _make_blueprint()
        er = _make_execution_report("SUCCESS")
        dr = _make_delivery_report("HEALTHY")
        report = self.engine.archive_project(project, self.cos, delivery_report=dr,
                                              execution_reports=[er], blueprint=bp)
        ka = report.knowledge_assets[0]
        d = ka.to_dict()
        self.assertIn("knowledge_id", d)
        self.assertIn("lessons_learned", d)
        self.assertIn("best_practices", d)
        self.assertIn("reusable_assets", d)
        self.assertIn("patterns", d)

    def test_lesson_serialization(self) -> None:
        ll = LessonLearned(
            lesson_id="LL-0001", title="Test lesson", description="desc",
            confidence=KnowledgeConfidence.VALIDATED, source_project_ids=["PROJ-0001"],
        )
        d = ll.to_dict()
        self.assertEqual(d["lesson_id"], "LL-0001")
        self.assertEqual(d["confidence"], "VALIDATED")

    def test_best_practice_serialization(self) -> None:
        bp = BestPractice(
            practice_id="BP-0001", title="Test practice", description="desc",
            applicability="all", source_project_ids=["PROJ-0001"],
        )
        d = bp.to_dict()
        self.assertEqual(d["practice_id"], "BP-0001")

    def test_reusable_asset_serialization(self) -> None:
        ra = ReusableAsset(
            asset_id="RA-0001", title="Template", asset_type="TEMPLATE",
            content="template content", source_project_ids=["PROJ-0001"],
        )
        d = ra.to_dict()
        self.assertEqual(d["asset_id"], "RA-0001")
        self.assertEqual(d["asset_type"], "TEMPLATE")

    def test_project_pattern_serialization(self) -> None:
        pt = ProjectPattern(
            pattern_id="PT-0001", title="Delivery Pattern",
            description="A pattern", industry="SOFTWARE", complexity="High",
            team_size=3, delivery_phases=["Setup", "Build", "Deploy"],
            source_project_ids=["PROJ-0001"],
        )
        d = pt.to_dict()
        self.assertEqual(d["pattern_id"], "PT-0001")
        self.assertEqual(d["team_size"], 3)

    # ------------------------------------------------------------------
    # Edge Cases
    # ------------------------------------------------------------------

    def test_empty_work_orders_no_crash(self) -> None:
        project = _make_completed_project("PROJ-E001")
        # project.work_orders is already []
        report = self.engine.archive_project(project, self.cos)
        self.assertIsNotNone(report)

    def test_empty_deliverables_no_crash(self) -> None:
        project = _make_completed_project("PROJ-E002")
        report = self.engine.archive_project(project, self.cos)
        ka = report.knowledge_assets[0]
        # No deliverable templates expected
        template_assets = [ra for ra in ka.reusable_assets if ra.asset_type == "TEMPLATE"]
        self.assertEqual(len(template_assets), 0)

    def test_incrementing_knowledge_ids(self) -> None:
        engine = OrganizationalMemoryEngine()
        kr = KnowledgeRegistry()
        cos = _make_chief_of_staff(kr)

        p1 = _make_completed_project("PROJ-INC001")
        p2 = _make_completed_project("PROJ-INC002")
        r1 = engine.archive_project(p1, cos)
        r2 = engine.archive_project(p2, cos)
        id1 = r1.knowledge_assets[0].knowledge_id
        id2 = r2.knowledge_assets[0].knowledge_id
        self.assertNotEqual(id1, id2)
        self.assertLess(id1, id2)  # KN-000001 < KN-000002 lexicographically

    def test_report_summary_counts(self) -> None:
        project = _make_completed_project("PROJ-CNT001")
        dr = _make_delivery_report("HEALTHY")
        er = _make_execution_report("SUCCESS")
        bp = _make_blueprint()
        report = self.engine.archive_project(project, self.cos, delivery_report=dr,
                                              execution_reports=[er], blueprint=bp)
        summary = report.summary()
        self.assertGreaterEqual(summary["total_best_practices"], 1)
        self.assertGreaterEqual(summary["total_reusable_assets"], 1)

    def test_knowledge_category_from_string(self) -> None:
        self.assertEqual(KnowledgeCategory.from_string("education"), KnowledgeCategory.EDUCATION)
        self.assertEqual(KnowledgeCategory.from_string("UNKNOWN_XYZ"), KnowledgeCategory.GENERAL)
        self.assertEqual(KnowledgeCategory.from_string(""), KnowledgeCategory.GENERAL)


if __name__ == "__main__":
    unittest.main()
