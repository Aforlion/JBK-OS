from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from core.knowledge_registry import KnowledgeRegistry
from core.organizational_knowledge import (
    KnowledgeConfidence,
    LessonLearned,
    BestPractice,
    ReusableAsset,
    OrganizationalKnowledge,
)
from core.continuous_improvement_report import (
    ImprovementCategory,
    ImprovementPriority,
    ContinuousImprovementRecommendation,
    ContinuousImprovementReport,
)

LOGGER = logging.getLogger(__name__)

# BR-031-001: minimum occurrences for a non-critical pattern recommendation
_MIN_PATTERN_OCCURRENCES = 2


class ContinuousImprovementEngine:
    """Stateless engine that analyses accumulated OrganizationalKnowledge and
    produces actionable improvement recommendations for JBK OS.

    Business Rules enforced:
        BR-031-001: Evidence-based; no single-event recommendation without CRITICAL flag.
        BR-031-002: Recurring observations grouped into patterns.
        BR-031-003: Every recommendation carries supporting evidence with source references.
        BR-031-004: Every recommendation carries a confidence level.
        BR-031-005: Recommendations are categorized.
        BR-031-006: Never modifies company documents.
        BR-031-007: Recommendations require executive approval (advisory only).
        BR-031-008: Every recommendation traceable to source knowledge.
        BR-031-009: Report serializes completely.
    """

    def __init__(self) -> None:
        self._report_counter = 1
        self._rec_counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        knowledge_registry: KnowledgeRegistry,
        ceo_notes: list[str] | None = None,
    ) -> ContinuousImprovementReport:
        """Analyse all knowledge in the registry and produce an improvement report."""
        if knowledge_registry is None:
            raise ValueError("Knowledge Registry is required.")

        report_id = self._next_report_id()
        LOGGER.info(
            "object_id=%s action=analyze actor=system status=DRAFT", report_id
        )

        knowledge_assets: list[OrganizationalKnowledge] = [
            item for item in knowledge_registry.list_items()
            if isinstance(item, OrganizationalKnowledge)
        ]

        warnings: list[str] = []
        if not knowledge_assets:
            warnings.append("No OrganizationalKnowledge assets found in registry. Nothing to analyze.")
            return ContinuousImprovementReport(
                report_id=report_id,
                knowledge_assets_analyzed=0,
                lessons_analyzed=0,
                recommendations=[],
                recurring_problems=[],
                recurring_successes=[],
                standards_to_update=[],
                sop_recommendations=[],
                template_recommendations=[],
                specification_recommendations=[],
                skill_recommendations=[],
                warnings=warnings,
            )

        # Flatten all sub-objects across all knowledge assets
        all_lessons: list[tuple[LessonLearned, str]] = []       # (lesson, knowledge_id)
        all_practices: list[tuple[BestPractice, str]] = []      # (practice, knowledge_id)
        all_assets: list[tuple[ReusableAsset, str]] = []        # (asset, knowledge_id)
        all_project_ids: set[str] = set()

        for ka in knowledge_assets:
            for ll in ka.lessons_learned:
                all_lessons.append((ll, ka.knowledge_id))
            for bp in ka.best_practices:
                all_practices.append((bp, ka.knowledge_id))
            for ra in ka.reusable_assets:
                all_assets.append((ra, ka.knowledge_id))
            all_project_ids.update(ka.source_project_ids)

        # ---- Analysis passes -----------------------------------------------
        recurring_problems = self._detect_recurring_problems(all_lessons)
        recurring_successes = self._detect_recurring_successes(all_practices)

        recommendations: list[ContinuousImprovementRecommendation] = []

        # 1. Process improvement from recurring problems
        recommendations.extend(
            self._recommend_process_improvements(recurring_problems, all_lessons)
        )

        # 2. Standards recommendations from proven best practices
        recommendations.extend(
            self._recommend_standards(recurring_successes, all_practices)
        )

        # 3. Template recommendations from reusable assets
        template_recs = self._recommend_templates(all_assets)
        recommendations.extend(template_recs)

        # 4. Skill gap recommendations from recurring lessons mentioning missing capabilities
        skill_recs = self._recommend_skills(all_lessons)
        recommendations.extend(skill_recs)

        # 5. Specification update recommendations from patterns
        spec_recs = self._recommend_spec_updates(knowledge_assets)
        recommendations.extend(spec_recs)

        # 6. CEO notes → operational improvement recommendations
        if ceo_notes:
            recommendations.extend(
                self._recommendations_from_ceo_notes(ceo_notes, knowledge_assets)
            )
        else:
            warnings.append("No CEO notes provided; operational recommendations derived from knowledge only.")

        # Sort recommendations: CRITICAL → HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.CRITICAL: 0,
            ImprovementPriority.HIGH: 1,
            ImprovementPriority.MEDIUM: 2,
            ImprovementPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        # ---- Structured output lists ----------------------------------------
        standards_to_update = [
            {"title": r.title, "recommendation_id": r.recommendation_id, "evidence_count": len(r.evidence)}
            for r in recommendations
            if r.category == ImprovementCategory.KNOWLEDGE and r.priority in (
                ImprovementPriority.HIGH, ImprovementPriority.CRITICAL
            )
        ]

        sop_recs = [
            {"title": r.title, "recommendation_id": r.recommendation_id, "action_items": r.action_items}
            for r in recommendations
            if r.category == ImprovementCategory.PROCESS
        ]

        template_output = [
            {"title": r.title, "recommendation_id": r.recommendation_id}
            for r in recommendations
            if r.category == ImprovementCategory.OPERATIONS
        ]

        spec_output = [
            {"title": r.title, "recommendation_id": r.recommendation_id, "priority": r.priority.value}
            for r in recommendations
            if r.category == ImprovementCategory.ARCHITECTURE
        ]

        skill_output = [
            {"title": r.title, "recommendation_id": r.recommendation_id, "priority": r.priority.value}
            for r in recommendations
            if r.category == ImprovementCategory.TRAINING
        ]

        LOGGER.info(
            "object_id=%s action=analyze actor=system status=READY "
            "assets=%d lessons=%d recommendations=%d",
            report_id,
            len(knowledge_assets),
            len(all_lessons),
            len(recommendations),
        )

        return ContinuousImprovementReport(
            report_id=report_id,
            knowledge_assets_analyzed=len(knowledge_assets),
            lessons_analyzed=len(all_lessons),
            recommendations=recommendations,
            recurring_problems=recurring_problems,
            recurring_successes=recurring_successes,
            standards_to_update=standards_to_update,
            sop_recommendations=sop_recs,
            template_recommendations=template_output,
            specification_recommendations=spec_output,
            skill_recommendations=skill_output,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    def _detect_recurring_problems(
        self,
        all_lessons: list[tuple[LessonLearned, str]],
    ) -> list[dict[str, Any]]:
        """Group lessons by normalized title to surface recurring problems (BR-031-002)."""
        title_map: dict[str, list[tuple[LessonLearned, str]]] = {}
        for ll, kid in all_lessons:
            key = ll.title.strip().lower()
            title_map.setdefault(key, []).append((ll, kid))

        problems = []
        for key, occurrences in title_map.items():
            if len(occurrences) >= _MIN_PATTERN_OCCURRENCES:
                sample_lesson = occurrences[0][0]
                source_kids = list({kid for _, kid in occurrences})
                source_pids = list({
                    pid for ll, _ in occurrences for pid in ll.source_project_ids
                })
                problems.append({
                    "title": sample_lesson.title,
                    "description": sample_lesson.description,
                    "occurrence_count": len(occurrences),
                    "source_knowledge_ids": source_kids,
                    "source_project_ids": source_pids,
                    "confidence": sample_lesson.confidence.value,
                    "category": sample_lesson.category.value,
                })
        return problems

    def _detect_recurring_successes(
        self,
        all_practices: list[tuple[BestPractice, str]],
    ) -> list[dict[str, Any]]:
        """Group best practices by normalized title to surface recurring successes."""
        title_map: dict[str, list[tuple[BestPractice, str]]] = {}
        for bp, kid in all_practices:
            key = bp.title.strip().lower()
            title_map.setdefault(key, []).append((bp, kid))

        successes = []
        for key, occurrences in title_map.items():
            if len(occurrences) >= _MIN_PATTERN_OCCURRENCES:
                sample = occurrences[0][0]
                source_kids = list({kid for _, kid in occurrences})
                source_pids = list({
                    pid for bp, _ in occurrences for pid in bp.source_project_ids
                })
                successes.append({
                    "title": sample.title,
                    "description": sample.description,
                    "occurrence_count": len(occurrences),
                    "source_knowledge_ids": source_kids,
                    "source_project_ids": source_pids,
                    "confidence": sample.confidence.value,
                })
        return successes

    # ------------------------------------------------------------------
    # Recommendation builders
    # ------------------------------------------------------------------

    def _recommend_process_improvements(
        self,
        recurring_problems: list[dict[str, Any]],
        all_lessons: list[tuple[LessonLearned, str]],
    ) -> list[ContinuousImprovementRecommendation]:
        recs: list[ContinuousImprovementRecommendation] = []
        for problem in recurring_problems:
            evidence = [
                {
                    "source": f"Project {pid}",
                    "lesson": problem["title"],
                }
                for pid in problem["source_project_ids"]
            ]
            priority = ImprovementPriority.from_confidence(problem["confidence"])
            if problem["occurrence_count"] >= 4:
                priority = ImprovementPriority.CRITICAL
            elif problem["occurrence_count"] >= 3:
                priority = ImprovementPriority.HIGH

            recs.append(ContinuousImprovementRecommendation(
                recommendation_id=self._next_rec_id(),
                title=f"Process Improvement: {problem['title']}",
                description=(
                    f"This issue recurred {problem['occurrence_count']} time(s) across "
                    f"{len(problem['source_project_ids'])} project(s). "
                    f"Review and update the relevant process or SOP to address root cause."
                ),
                category=ImprovementCategory.PROCESS,
                priority=priority,
                confidence=problem["confidence"],
                evidence=evidence,
                source_knowledge_ids=problem["source_knowledge_ids"],
                source_project_ids=problem["source_project_ids"],
                action_items=[
                    f"Identify root cause of: {problem['title']}",
                    "Draft SOP update or new procedure",
                    "Submit for executive review",
                ],
                tags=["recurring-problem", "process", problem["category"].lower()],
            ))
        return recs

    def _recommend_standards(
        self,
        recurring_successes: list[dict[str, Any]],
        all_practices: list[tuple[BestPractice, str]],
    ) -> list[ContinuousImprovementRecommendation]:
        recs: list[ContinuousImprovementRecommendation] = []
        for success in recurring_successes:
            evidence = [
                {"source": f"Project {pid}", "practice": success["title"]}
                for pid in success["source_project_ids"]
            ]
            recs.append(ContinuousImprovementRecommendation(
                recommendation_id=self._next_rec_id(),
                title=f"Promote to Standard: {success['title']}",
                description=(
                    f"This practice succeeded {success['occurrence_count']} time(s) across "
                    f"{len(success['source_project_ids'])} project(s). "
                    f"Candidate for promotion to a JBK company standard or playbook entry."
                ),
                category=ImprovementCategory.KNOWLEDGE,
                priority=ImprovementPriority.from_confidence(success["confidence"]),
                confidence=success["confidence"],
                evidence=evidence,
                source_knowledge_ids=success["source_knowledge_ids"],
                source_project_ids=success["source_project_ids"],
                action_items=[
                    f"Draft standard document for: {success['title']}",
                    "Submit to Knowledge Curator for review",
                    "Obtain executive approval before publishing",
                ],
                tags=["recurring-success", "standards", "knowledge"],
            ))
        return recs

    def _recommend_templates(
        self,
        all_assets: list[tuple[ReusableAsset, str]],
    ) -> list[ContinuousImprovementRecommendation]:
        """Recommend formalising frequently appearing reusable asset types."""
        type_counter: Counter = Counter(ra.asset_type for ra, _ in all_assets)
        recs: list[ContinuousImprovementRecommendation] = []

        for asset_type, count in type_counter.items():
            if count >= _MIN_PATTERN_OCCURRENCES:
                matching = [(ra, kid) for ra, kid in all_assets if ra.asset_type == asset_type]
                source_kids = list({kid for _, kid in matching})
                source_pids = list({pid for ra, _ in matching for pid in ra.source_project_ids})
                evidence = [{"source": f"Project {pid}", "asset_type": asset_type}
                            for pid in source_pids]

                recs.append(ContinuousImprovementRecommendation(
                    recommendation_id=self._next_rec_id(),
                    title=f"Standardise {asset_type} Template Library",
                    description=(
                        f"{count} reusable {asset_type} asset(s) have been produced across "
                        f"{len(source_pids)} project(s). Consider formalising these into a "
                        f"shared template library for future reuse."
                    ),
                    category=ImprovementCategory.OPERATIONS,
                    priority=ImprovementPriority.MEDIUM,
                    confidence="VALIDATED",
                    evidence=evidence,
                    source_knowledge_ids=source_kids,
                    source_project_ids=source_pids,
                    action_items=[
                        f"Collect all {asset_type} assets from knowledge registry",
                        "Curate and version-control into shared template library",
                        "Link to relevant SOPs and playbooks",
                    ],
                    tags=["template", "reusable", asset_type.lower()],
                ))
        return recs

    def _recommend_skills(
        self,
        all_lessons: list[tuple[LessonLearned, str]],
    ) -> list[ContinuousImprovementRecommendation]:
        """Surface training/skill gap recommendations from lessons tagged with failure or blocker."""
        skill_gap_lessons: list[tuple[LessonLearned, str]] = [
            (ll, kid) for ll, kid in all_lessons
            if any(t in (ll.tags or []) for t in ["failure", "blocker", "missing-worker"])
        ]

        if not skill_gap_lessons:
            return []

        source_kids = list({kid for _, kid in skill_gap_lessons})
        source_pids = list({pid for ll, _ in skill_gap_lessons for pid in ll.source_project_ids})
        evidence = [
            {"source": f"Project {pid}", "lesson": ll.title}
            for ll, _ in skill_gap_lessons
            for pid in ll.source_project_ids
        ][:10]  # cap evidence list

        return [ContinuousImprovementRecommendation(
            recommendation_id=self._next_rec_id(),
            title="Skill Gap: Review Execution Capability Coverage",
            description=(
                f"{len(skill_gap_lessons)} lesson(s) indicate execution failures or resource "
                f"blockers across {len(source_pids)} project(s). "
                "Review workforce capabilities and consider targeted training or new skill definitions."
            ),
            category=ImprovementCategory.TRAINING,
            priority=ImprovementPriority.HIGH if len(skill_gap_lessons) >= 3 else ImprovementPriority.MEDIUM,
            confidence="VALIDATED",
            evidence=evidence,
            source_knowledge_ids=source_kids,
            source_project_ids=source_pids,
            action_items=[
                "Audit current skill registry for coverage gaps",
                "Identify top 3 missing capabilities from lesson patterns",
                "Propose training programme or new executive hire",
            ],
            tags=["skill-gap", "training", "execution"],
        )]

    def _recommend_spec_updates(
        self,
        knowledge_assets: list[OrganizationalKnowledge],
    ) -> list[ContinuousImprovementRecommendation]:
        """Recommend specification or architecture updates based on pattern data."""
        # Surface assets whose patterns show high complexity consistently
        high_complexity_assets = [
            ka for ka in knowledge_assets
            if any(
                pt.complexity.upper() in ("HIGH", "VERY HIGH")
                for pt in ka.patterns
            )
        ]

        if len(high_complexity_assets) < _MIN_PATTERN_OCCURRENCES:
            return []

        source_kids = [ka.knowledge_id for ka in high_complexity_assets]
        source_pids = list({pid for ka in high_complexity_assets for pid in ka.source_project_ids})
        evidence = [
            {"source": f"Project {pid}", "finding": "High complexity delivery pattern"}
            for pid in source_pids
        ]

        return [ContinuousImprovementRecommendation(
            recommendation_id=self._next_rec_id(),
            title="Architecture Review: High-Complexity Delivery Patterns Detected",
            description=(
                f"{len(high_complexity_assets)} project(s) exhibit high-complexity delivery patterns. "
                "Review JBK OS specifications and architecture standards to determine whether "
                "additional tooling, guardrails, or decomposition strategies are needed."
            ),
            category=ImprovementCategory.ARCHITECTURE,
            priority=ImprovementPriority.HIGH,
            confidence="VALIDATED",
            evidence=evidence,
            source_knowledge_ids=source_kids,
            source_project_ids=source_pids,
            action_items=[
                "Review high-complexity project patterns in knowledge registry",
                "Identify common structural causes",
                "Draft specification update proposal for executive review",
            ],
            tags=["architecture", "complexity", "specification"],
        )]

    def _recommendations_from_ceo_notes(
        self,
        ceo_notes: list[str],
        knowledge_assets: list[OrganizationalKnowledge],
    ) -> list[ContinuousImprovementRecommendation]:
        """Convert CEO notes into operational improvement recommendations."""
        recs: list[ContinuousImprovementRecommendation] = []
        source_kids = [ka.knowledge_id for ka in knowledge_assets]
        source_pids = list({pid for ka in knowledge_assets for pid in ka.source_project_ids})

        for note in ceo_notes:
            note = note.strip()
            if not note:
                continue
            evidence = [{"source": "CEO Note", "note": note}]
            recs.append(ContinuousImprovementRecommendation(
                recommendation_id=self._next_rec_id(),
                title=f"CEO Directive: {note[:60]}{'...' if len(note) > 60 else ''}",
                description=(
                    f"CEO-identified operational improvement: {note} "
                    "Requires executive review and approval before implementation."
                ),
                category=ImprovementCategory.OPERATIONS,
                priority=ImprovementPriority.HIGH,
                confidence="VALIDATED",
                evidence=evidence,
                source_knowledge_ids=source_kids,
                source_project_ids=source_pids,
                action_items=[
                    "Review CEO directive in context of current operations",
                    "Draft improvement proposal",
                    "Obtain executive sign-off before executing",
                ],
                tags=["ceo-directive", "operations"],
                is_critical_single_event=True,
            ))
        return recs

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def _rec_id_prefix(self) -> str:
        return "IMP"

    def _next_rec_id(self) -> str:
        rid = f"IMP-{self._rec_counter:04d}"
        self._rec_counter += 1
        return rid

    def _next_report_id(self) -> str:
        rid = f"CIR-{self._report_counter:04d}"
        self._report_counter += 1
        return rid
