import unittest

from core.knowledge_registry import KnowledgeRegistry
from core.organizational_knowledge import (
    KnowledgeCategory,
    KnowledgeConfidence,
    LessonLearned,
    BestPractice,
    ReusableAsset,
    ProjectPattern,
    OrganizationalKnowledge,
)
from core.continuous_improvement_report import (
    ImprovementCategory,
    ImprovementPriority,
    ContinuousImprovementRecommendation,
    ContinuousImprovementReport,
)
from core.continuous_improvement_engine import ContinuousImprovementEngine


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _make_lesson(
    lesson_id: str,
    title: str = "Blocker: WAIT_LOCK",
    confidence: KnowledgeConfidence = KnowledgeConfidence.VALIDATED,
    source_project_ids: list[str] | None = None,
    tags: list[str] | None = None,
) -> LessonLearned:
    return LessonLearned(
        lesson_id=lesson_id,
        title=title,
        description=f"Description for {title}",
        confidence=confidence,
        source_project_ids=source_project_ids or ["PROJ-0001"],
        tags=tags or [],
    )


def _make_practice(
    practice_id: str,
    title: str = "Successful Execution via Antigravity",
    confidence: KnowledgeConfidence = KnowledgeConfidence.PROVEN,
    source_project_ids: list[str] | None = None,
) -> BestPractice:
    return BestPractice(
        practice_id=practice_id,
        title=title,
        description="A proven practice.",
        applicability="All projects",
        source_project_ids=source_project_ids or ["PROJ-0001"],
        confidence=confidence,
    )


def _make_asset(
    asset_id: str,
    asset_type: str = "TEMPLATE",
    source_project_ids: list[str] | None = None,
) -> ReusableAsset:
    return ReusableAsset(
        asset_id=asset_id,
        title=f"Asset {asset_id}",
        asset_type=asset_type,
        content="content",
        source_project_ids=source_project_ids or ["PROJ-0001"],
    )


def _make_pattern(
    pattern_id: str,
    complexity: str = "High",
    source_project_ids: list[str] | None = None,
) -> ProjectPattern:
    return ProjectPattern(
        pattern_id=pattern_id,
        title=f"Pattern {pattern_id}",
        description="A delivery pattern",
        industry="SOFTWARE",
        complexity=complexity,
        team_size=3,
        delivery_phases=["Setup", "Build"],
        source_project_ids=source_project_ids or ["PROJ-0001"],
    )


def _make_knowledge(
    knowledge_id: str,
    lessons: list[LessonLearned] | None = None,
    practices: list[BestPractice] | None = None,
    assets: list[ReusableAsset] | None = None,
    patterns: list[ProjectPattern] | None = None,
    source_project_ids: list[str] | None = None,
) -> OrganizationalKnowledge:
    return OrganizationalKnowledge(
        knowledge_id=knowledge_id,
        title=f"Knowledge {knowledge_id}",
        category=KnowledgeCategory.SOFTWARE,
        source_project_ids=source_project_ids or ["PROJ-0001"],
        lessons_learned=lessons or [],
        best_practices=practices or [],
        reusable_assets=assets or [],
        patterns=patterns or [],
    )


def _make_registry(*knowledge_assets: OrganizationalKnowledge) -> KnowledgeRegistry:
    registry = KnowledgeRegistry()
    for ka in knowledge_assets:
        registry.register(ka)
    return registry


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

class TestContinuousImprovementEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = ContinuousImprovementEngine()

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    def test_rejects_none_registry(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.analyze(None)  # type: ignore

    def test_empty_registry_returns_report_with_warning(self) -> None:
        registry = KnowledgeRegistry()
        report = self.engine.analyze(registry)
        self.assertIsInstance(report, ContinuousImprovementReport)
        self.assertEqual(report.knowledge_assets_analyzed, 0)
        self.assertEqual(len(report.recommendations), 0)
        self.assertGreater(len(report.warnings), 0)

    def test_non_knowledge_items_ignored(self) -> None:
        """Items that are not OrganizationalKnowledge should be skipped gracefully."""
        registry = KnowledgeRegistry()
        # Register a plain KnowledgeItem (different type) — engine should ignore it
        from core.knowledge import KnowledgeItem
        item = KnowledgeItem(
            knowledge_id="KI-0001", title="Raw item", category="SOFTWARE",
            owner="system", source="manual", tags=[], description="desc", version="1.0",
        )
        registry.register(item)
        report = self.engine.analyze(registry)
        self.assertEqual(report.knowledge_assets_analyzed, 0)

    # ------------------------------------------------------------------
    # Report Structure
    # ------------------------------------------------------------------

    def test_report_id_format(self) -> None:
        ka = _make_knowledge("KN-000001")
        report = self.engine.analyze(_make_registry(ka))
        self.assertTrue(report.report_id.startswith("CIR-"))

    def test_report_counts_assets_and_lessons(self) -> None:
        ll1 = _make_lesson("LL-0001")
        ka = _make_knowledge("KN-000001", lessons=[ll1])
        report = self.engine.analyze(_make_registry(ka))
        self.assertEqual(report.knowledge_assets_analyzed, 1)
        self.assertEqual(report.lessons_analyzed, 1)

    # ------------------------------------------------------------------
    # Recurring Problem Detection (BR-031-002)
    # ------------------------------------------------------------------

    def test_recurring_problem_requires_two_occurrences(self) -> None:
        """A single occurrence should NOT produce a recurring problem."""
        ll = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ka = _make_knowledge("KN-000001", lessons=[ll])
        report = self.engine.analyze(_make_registry(ka))
        self.assertEqual(len(report.recurring_problems), 0)

    def test_recurring_problem_detected_across_two_assets(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        self.assertEqual(len(report.recurring_problems), 1)
        self.assertEqual(report.recurring_problems[0]["occurrence_count"], 2)

    def test_recurring_problem_source_references(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Risk: API latency", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Risk: API latency", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        problem = report.recurring_problems[0]
        self.assertIn("PROJ-A", problem["source_project_ids"])
        self.assertIn("PROJ-B", problem["source_project_ids"])

    # ------------------------------------------------------------------
    # Recurring Success Detection
    # ------------------------------------------------------------------

    def test_recurring_success_requires_two_occurrences(self) -> None:
        bp = _make_practice("BP-0001")
        ka = _make_knowledge("KN-000001", practices=[bp])
        report = self.engine.analyze(_make_registry(ka))
        self.assertEqual(len(report.recurring_successes), 0)

    def test_recurring_success_detected_across_two_assets(self) -> None:
        bp1 = _make_practice("BP-0001", title="Deliverable Approval Workflow", source_project_ids=["PROJ-A"])
        bp2 = _make_practice("BP-0002", title="Deliverable Approval Workflow", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", practices=[bp1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", practices=[bp2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        self.assertEqual(len(report.recurring_successes), 1)

    # ------------------------------------------------------------------
    # Process Improvement Recommendations (BR-031-001, 003, 004, 008)
    # ------------------------------------------------------------------

    def test_process_recommendation_generated_from_recurring_problem(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        process_recs = [r for r in report.recommendations if r.category == ImprovementCategory.PROCESS]
        self.assertGreater(len(process_recs), 0)

    def test_recommendation_has_evidence(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Risk: slow deploy", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Risk: slow deploy", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        for rec in report.recommendations:
            self.assertGreater(len(rec.evidence), 0, f"Recommendation '{rec.title}' has no evidence")

    def test_recommendation_has_source_knowledge_ids(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Failure: timeout", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Failure: timeout", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        for rec in report.recommendations:
            self.assertGreater(len(rec.source_knowledge_ids), 0)

    def test_priority_escalates_with_occurrence_count(self) -> None:
        """4+ occurrences should yield CRITICAL priority."""
        lessons = [
            _make_lesson(f"LL-{i:04d}", title="Blocker: WAIT_LOCK", source_project_ids=[f"PROJ-{i}"])
            for i in range(4)
        ]
        kas = [
            _make_knowledge(f"KN-{i:06d}", lessons=[lessons[i]], source_project_ids=[f"PROJ-{i}"])
            for i in range(4)
        ]
        report = self.engine.analyze(_make_registry(*kas))
        process_recs = [r for r in report.recommendations if r.category == ImprovementCategory.PROCESS]
        self.assertTrue(any(r.priority == ImprovementPriority.CRITICAL for r in process_recs))

    # ------------------------------------------------------------------
    # Standards Recommendations
    # ------------------------------------------------------------------

    def test_standards_recommendation_from_recurring_success(self) -> None:
        bp1 = _make_practice("BP-0001", title="Deliverable Approval Workflow", source_project_ids=["PROJ-A"])
        bp2 = _make_practice("BP-0002", title="Deliverable Approval Workflow", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", practices=[bp1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", practices=[bp2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        knowledge_recs = [r for r in report.recommendations if r.category == ImprovementCategory.KNOWLEDGE]
        self.assertGreater(len(knowledge_recs), 0)
        # standards_to_update is a list of dicts with recommendation_id keys
        self.assertGreater(len(report.standards_to_update), 0)
        self.assertIn("recommendation_id", report.standards_to_update[0])

    # ------------------------------------------------------------------
    # Template Recommendations
    # ------------------------------------------------------------------

    def test_template_recommendation_from_repeated_asset_type(self) -> None:
        ra1 = _make_asset("RA-0001", asset_type="TEMPLATE", source_project_ids=["PROJ-A"])
        ra2 = _make_asset("RA-0002", asset_type="TEMPLATE", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", assets=[ra1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", assets=[ra2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        ops_recs = [r for r in report.recommendations if r.category == ImprovementCategory.OPERATIONS]
        self.assertGreater(len(ops_recs), 0)
        self.assertTrue(any("TEMPLATE" in r.title for r in ops_recs))

    def test_no_template_recommendation_for_single_asset(self) -> None:
        ra = _make_asset("RA-0001", asset_type="ARCHITECTURE")
        ka = _make_knowledge("KN-000001", assets=[ra])
        report = self.engine.analyze(_make_registry(ka))
        template_recs = [r for r in report.recommendations
                        if r.category == ImprovementCategory.OPERATIONS and "ARCHITECTURE" in r.title]
        self.assertEqual(len(template_recs), 0)

    # ------------------------------------------------------------------
    # Skill Recommendations
    # ------------------------------------------------------------------

    def test_skill_recommendation_from_failure_tagged_lessons(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Exec Fail A", tags=["failure"], source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Exec Fail B", tags=["failure"], source_project_ids=["PROJ-B"])
        ll3 = _make_lesson("LL-0003", title="Exec Fail C", tags=["failure"], source_project_ids=["PROJ-C"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        ka3 = _make_knowledge("KN-000003", lessons=[ll3], source_project_ids=["PROJ-C"])
        report = self.engine.analyze(_make_registry(ka1, ka2, ka3))
        training_recs = [r for r in report.recommendations if r.category == ImprovementCategory.TRAINING]
        self.assertGreater(len(training_recs), 0)
        self.assertEqual(training_recs[0].priority, ImprovementPriority.HIGH)

    def test_no_skill_recommendation_without_failure_tags(self) -> None:
        ll = _make_lesson("LL-0001", title="Generic lesson", tags=[], source_project_ids=["PROJ-A"])
        ka = _make_knowledge("KN-000001", lessons=[ll])
        report = self.engine.analyze(_make_registry(ka))
        training_recs = [r for r in report.recommendations if r.category == ImprovementCategory.TRAINING]
        self.assertEqual(len(training_recs), 0)

    # ------------------------------------------------------------------
    # Architecture / Specification Recommendations
    # ------------------------------------------------------------------

    def test_architecture_recommendation_from_high_complexity_patterns(self) -> None:
        pt1 = _make_pattern("PT-0001", complexity="High", source_project_ids=["PROJ-A"])
        pt2 = _make_pattern("PT-0002", complexity="High", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", patterns=[pt1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", patterns=[pt2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        arch_recs = [r for r in report.recommendations if r.category == ImprovementCategory.ARCHITECTURE]
        self.assertGreater(len(arch_recs), 0)

    def test_no_architecture_recommendation_for_low_complexity(self) -> None:
        pt1 = _make_pattern("PT-0001", complexity="Low", source_project_ids=["PROJ-A"])
        pt2 = _make_pattern("PT-0002", complexity="Low", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", patterns=[pt1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", patterns=[pt2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        arch_recs = [r for r in report.recommendations if r.category == ImprovementCategory.ARCHITECTURE]
        self.assertEqual(len(arch_recs), 0)

    # ------------------------------------------------------------------
    # CEO Notes
    # ------------------------------------------------------------------

    def test_ceo_notes_produce_operations_recommendations(self) -> None:
        ka = _make_knowledge("KN-000001")
        report = self.engine.analyze(_make_registry(ka), ceo_notes=["Always run a post-mortem."])
        ops_recs = [r for r in report.recommendations if r.category == ImprovementCategory.OPERATIONS]
        self.assertGreater(len(ops_recs), 0)
        self.assertTrue(any("post-mortem" in r.description for r in ops_recs))

    def test_warning_on_missing_ceo_notes(self) -> None:
        ka = _make_knowledge("KN-000001")
        report = self.engine.analyze(_make_registry(ka), ceo_notes=None)
        self.assertTrue(any("CEO notes" in w for w in report.warnings))

    # ------------------------------------------------------------------
    # Priority Ordering
    # ------------------------------------------------------------------

    def test_recommendations_sorted_by_priority(self) -> None:
        """CRITICAL and HIGH recommendations must appear before LOW."""
        ll1 = _make_lesson("LL-0001", title="Critical Issue", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Critical Issue", source_project_ids=["PROJ-B"])
        ll3 = _make_lesson("LL-0003", title="Critical Issue", source_project_ids=["PROJ-C"])
        ll4 = _make_lesson("LL-0004", title="Critical Issue", source_project_ids=["PROJ-D"])
        kas = [
            _make_knowledge(f"KN-{i:06d}", lessons=[l], source_project_ids=[l.source_project_ids[0]])
            for i, l in enumerate([ll1, ll2, ll3, ll4])
        ]
        report = self.engine.analyze(_make_registry(*kas))
        if len(report.recommendations) >= 2:
            priority_order = {
                ImprovementPriority.CRITICAL: 0,
                ImprovementPriority.HIGH: 1,
                ImprovementPriority.MEDIUM: 2,
                ImprovementPriority.LOW: 3,
            }
            scores = [priority_order[r.priority] for r in report.recommendations]
            self.assertEqual(scores, sorted(scores))

    # ------------------------------------------------------------------
    # BR-031-001: Evidence Required
    # ------------------------------------------------------------------

    def test_recommendation_requires_evidence(self) -> None:
        with self.assertRaises(ValueError):
            ContinuousImprovementRecommendation(
                recommendation_id="IMP-0001",
                title="Test rec",
                description="desc",
                category=ImprovementCategory.PROCESS,
                priority=ImprovementPriority.MEDIUM,
                confidence="VALIDATED",
                evidence=[],          # empty — must raise
                source_knowledge_ids=["KN-000001"],
                source_project_ids=["PROJ-0001"],
                is_critical_single_event=False,
            )

    def test_critical_single_event_bypasses_evidence_rule(self) -> None:
        rec = ContinuousImprovementRecommendation(
            recommendation_id="IMP-0002",
            title="Critical single event",
            description="desc",
            category=ImprovementCategory.OPERATIONS,
            priority=ImprovementPriority.CRITICAL,
            confidence="PROVEN",
            evidence=[],              # empty but CRITICAL override
            source_knowledge_ids=["KN-000001"],
            source_project_ids=["PROJ-0001"],
            is_critical_single_event=True,
        )
        self.assertTrue(rec.is_critical_single_event)

    # ------------------------------------------------------------------
    # BR-031-008: Traceability
    # ------------------------------------------------------------------

    def test_recommendation_requires_source_knowledge_id(self) -> None:
        with self.assertRaises(ValueError):
            ContinuousImprovementRecommendation(
                recommendation_id="IMP-0003",
                title="Missing trace",
                description="desc",
                category=ImprovementCategory.PROCESS,
                priority=ImprovementPriority.LOW,
                confidence="LOW",
                evidence=[{"source": "some evidence"}],
                source_knowledge_ids=[],   # missing — must raise
                source_project_ids=["PROJ-0001"],
            )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def test_recommendation_matches_by_title(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        process_recs = [r for r in report.recommendations if r.matches("WAIT_LOCK")]
        self.assertGreater(len(process_recs), 0)

    # ------------------------------------------------------------------
    # BR-031-009: Serialization
    # ------------------------------------------------------------------

    def test_report_serialization(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        d = report.to_dict()
        self.assertIn("report_id", d)
        self.assertIn("recommendations", d)
        self.assertIn("summary", d)

    def test_recommendation_serialization(self) -> None:
        rec = ContinuousImprovementRecommendation(
            recommendation_id="IMP-0001",
            title="Test",
            description="desc",
            category=ImprovementCategory.PROCESS,
            priority=ImprovementPriority.HIGH,
            confidence="VALIDATED",
            evidence=[{"source": "PROJ-A", "lesson": "Blocker"}],
            source_knowledge_ids=["KN-000001"],
            source_project_ids=["PROJ-A"],
        )
        d = rec.to_dict()
        self.assertEqual(d["recommendation_id"], "IMP-0001")
        self.assertEqual(d["category"], "PROCESS")
        self.assertEqual(d["priority"], "HIGH")

    def test_report_summary_structure(self) -> None:
        ka = _make_knowledge("KN-000001")
        report = self.engine.analyze(_make_registry(ka))
        s = report.summary()
        self.assertIn("total_recommendations", s)
        self.assertIn("by_category", s)
        self.assertIn("by_priority", s)
        self.assertIn("high_priority_count", s)

    # ------------------------------------------------------------------
    # Structured Output Lists
    # ------------------------------------------------------------------

    def test_sop_recommendations_populated_from_process_recs(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        self.assertGreater(len(report.sop_recommendations), 0)

    def test_by_category_grouping(self) -> None:
        ll1 = _make_lesson("LL-0001", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-A"])
        ll2 = _make_lesson("LL-0002", title="Blocker: WAIT_LOCK", source_project_ids=["PROJ-B"])
        ka1 = _make_knowledge("KN-000001", lessons=[ll1], source_project_ids=["PROJ-A"])
        ka2 = _make_knowledge("KN-000002", lessons=[ll2], source_project_ids=["PROJ-B"])
        report = self.engine.analyze(_make_registry(ka1, ka2))
        grouped = report.by_category
        self.assertIn("PROCESS", grouped)

    # ------------------------------------------------------------------
    # Enums
    # ------------------------------------------------------------------

    def test_improvement_category_from_string(self) -> None:
        self.assertEqual(ImprovementCategory.from_string("process"), ImprovementCategory.PROCESS)
        self.assertEqual(ImprovementCategory.from_string("TRAINING"), ImprovementCategory.TRAINING)
        self.assertEqual(ImprovementCategory.from_string("unknown_xyz"), ImprovementCategory.GENERAL)

    def test_improvement_priority_from_confidence(self) -> None:
        self.assertEqual(ImprovementPriority.from_confidence("PROVEN"), ImprovementPriority.HIGH)
        self.assertEqual(ImprovementPriority.from_confidence("VALIDATED"), ImprovementPriority.MEDIUM)
        self.assertEqual(ImprovementPriority.from_confidence("EXPERIMENTAL"), ImprovementPriority.LOW)

    def test_incrementing_report_ids(self) -> None:
        engine = ContinuousImprovementEngine()
        ka = _make_knowledge("KN-000001")
        r1 = engine.analyze(_make_registry(ka))
        ka2 = _make_knowledge("KN-000002")
        r2 = engine.analyze(_make_registry(ka2))
        self.assertNotEqual(r1.report_id, r2.report_id)


if __name__ == "__main__":
    unittest.main()
