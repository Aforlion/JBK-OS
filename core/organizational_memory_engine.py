from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.project import Project, ProjectStatus
from core.chief_of_staff import ChiefOfStaff
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
from core.memory_record import MemoryRecord
from core.memory_registry import MemoryRegistry

LOGGER = logging.getLogger(__name__)


class OrganizationalMemoryEngine:
    """Orchestrates building, capturing, recalling, and archiving organizational experiences."""

    def __init__(self, memory_registry: MemoryRegistry | None = None) -> None:
        self._knowledge_counter = 1
        self._lesson_counter = 1
        self._practice_counter = 1
        self._asset_counter = 1
        self._pattern_counter = 1
        self._report_counter = 1
        self.memory_registry = memory_registry or MemoryRegistry()

    # ------------------------------------------------------------------
    # Spec 042 Core Experience Memory Capture & Recall
    # ------------------------------------------------------------------

    def remember(
        self,
        category: str,
        title: str,
        summary: str,
        full_context: str,
        related_entities: list[str] | None = None,
        created_by: str = "system",
        confidence: float = 1.0,
        importance: int = 5,
        tags: list[str] | None = None,
        source_engine: str | None = None,
    ) -> MemoryRecord:
        """Capture a new experienced memory into the memory registry."""
        memory_id = f"MEM-{self._report_counter:04d}"
        self._report_counter += 1

        record = MemoryRecord(
            memory_id=memory_id,
            category=category,
            title=title,
            summary=summary,
            full_context=full_context,
            related_entities=related_entities,
            created_by=created_by,
            confidence=confidence,
            importance=importance,
            tags=tags,
            source_engine=source_engine,
        )
        self.memory_registry.register(record)
        return record

    def recall(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant experiences ranked by recency, importance, confidence, and query match.

        Each result includes explainability metadata ('explanation' list) and confidence percentage.
        """
        all_active = [m for m in self.memory_registry.list_items() if not m.archived]
        if category:
            all_active = [m for m in all_active if m.category == category.strip().lower()]

        scored_results: list[dict[str, Any]] = []
        for m in all_active:
            match_score = 0.0
            explanation = []

            # Check matching factors
            q_clean = query.strip().lower() if query else ""
            if q_clean:
                if q_clean in m.title.lower():
                    match_score += 0.5
                    explanation.append(f"✓ Match found in title: '{m.title}'")
                if q_clean in m.summary.lower():
                    match_score += 0.3
                    explanation.append("✓ Match found in summary text")
                if q_clean in m.full_context.lower():
                    match_score += 0.2
                    explanation.append("✓ Match found in full context")
                if any(q_clean in tag.lower() for tag in m.tags):
                    match_score += 0.4
                    explanation.append("✓ Match found in tags")
                if any(q_clean in entity.lower() for entity in m.related_entities):
                    match_score += 0.4
                    explanation.append("✓ Match found in related entities")

            # Category preference match
            if category and m.category == category.strip().lower():
                match_score += 0.1
                explanation.append(f"✓ Matches requested category '{category}'")

            # If a query was provided but no match found, skip or rank lowest
            if q_clean and match_score == 0.0:
                continue

            # Additional ranking elements
            # Importance: scale 1 to 10 to a 0.0 to 1.0 weight
            importance_weight = m.importance / 10.0
            if m.importance >= 8:
                explanation.append(f"✓ High importance experience (Rating: {m.importance}/10)")

            # Confidence: 0.0 to 1.0 weight
            confidence_weight = m.confidence
            if m.confidence >= 0.8:
                explanation.append(f"✓ High confidence level (Confidence: {int(m.confidence * 100)}%)")

            # Final Score calculation: matches (50%) + importance (30%) + confidence (20%)
            final_score = (match_score * 0.5) + (importance_weight * 0.3) + (confidence_weight * 0.2)

            scored_results.append({
                "record": m,
                "score": round(final_score, 3),
                "explanation": explanation if explanation else ["✓ Retrieved via general relevance scan"],
                "confidence_pct": int(m.confidence * 100),
            })

        # Sort by final score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:limit]

    # ------------------------------------------------------------------
    # Existing Stateless project archival methods (Keep for compatibility)
    # ------------------------------------------------------------------

    def archive_project(
        self,
        project: Project,
        chief_of_staff: ChiefOfStaff,
        delivery_report: DeliveryStatusReport | None = None,
        execution_reports: list[ExecutionReport] | None = None,
        blueprint: SolutionBlueprint | None = None,
        ceo_notes: list[str] | None = None,
    ) -> OrganizationalMemoryReport:
        """Archive a completed project into organizational knowledge.

        Business Rules:
            BR-030-001: Only completed projects may be archived.
            BR-030-002: Original project records are immutable.
            BR-030-008: The engine never edits historical projects.
        """
        if project is None:
            raise ValueError("Project is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        project_status = getattr(project.status, "value", project.status)
        if project_status != ProjectStatus.COMPLETED.value:
            raise ValueError(
                f"Only COMPLETED projects may be archived (BR-030-001). "
                f"Project {project.id} has status: {project_status}."
            )

        report_id = self._next_report_id()
        LOGGER.info(
            "object_id=%s action=archive_project actor=system status=DRAFT project_id=%s",
            report_id,
            project.id,
        )

        warnings: list[str] = []

        # Resolve category from blueprint metadata
        category = self._resolve_category(blueprint)

        # Determine confidence from execution and delivery data
        confidence = self._resolve_confidence(delivery_report, execution_reports)

        # ---- Extraction --------------------------------------------------
        lessons = self._extract_lessons(project, delivery_report, confidence, category)
        practices = self._extract_best_practices(project, execution_reports, confidence, category)
        assets = self._extract_reusable_assets(project, blueprint, category)
        pattern = self._extract_project_pattern(project, blueprint, category)
        case_study = self._build_case_study(project, blueprint, delivery_report)
        future_recommendations = self._build_future_recommendations(
            blueprint, delivery_report, ceo_notes
        )

        # Warn on missing optional inputs
        if delivery_report is None:
            warnings.append("No DeliveryStatusReport provided; lessons and risk data may be incomplete.")
        if not execution_reports:
            warnings.append("No ExecutionReports provided; best practices extracted from deliverables only.")
        if blueprint is None:
            warnings.append("No SolutionBlueprint provided; reusable assets and category defaulted to GENERAL.")
        if not ceo_notes:
            warnings.append("No CEO notes provided; future recommendations derived from blueprint risks only.")

        # ---- Assemble OrganizationalKnowledge record ---------------------
        knowledge_asset = OrganizationalKnowledge(
            knowledge_id=self._next_knowledge_id(),
            title=f"Project Knowledge: {project.title}",
            category=category,
            source_project_ids=[project.id],
            lessons_learned=lessons,
            best_practices=practices,
            reusable_assets=assets,
            patterns=[pattern] if pattern else [],
            case_study=case_study,
            future_recommendations=future_recommendations,
            tags=[project.client, category.value],
            description=(
                f"Organizational knowledge extracted from project '{project.title}' "
                f"for client '{project.client}'."
            ),
        )

        # ---- Delegate registration to Chief of Staff ---------------------
        chief_of_staff.register_knowledge(knowledge_asset)

        LOGGER.info(
            "object_id=%s action=archive_project actor=system status=READY project_id=%s "
            "knowledge_id=%s lessons=%d practices=%d assets=%d patterns=%d",
            report_id,
            project.id,
            knowledge_asset.knowledge_id,
            len(lessons),
            len(practices),
            len(assets),
            1 if pattern else 0,
        )

        return OrganizationalMemoryReport(
            report_id=report_id,
            project_id=project.id,
            knowledge_assets=[knowledge_asset],
            case_study=case_study,
            future_recommendations=future_recommendations,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    def _extract_lessons(
        self,
        project: Project,
        delivery_report: DeliveryStatusReport | None,
        confidence: KnowledgeConfidence,
        category: KnowledgeCategory,
    ) -> list[LessonLearned]:
        lessons: dict[str, LessonLearned] = {}

        # From delivery report blockers and risk register
        if delivery_report is not None:
            for blocker in delivery_report.blockers:
                title = f"Blocker: {blocker.get('type', 'Unknown')}"
                description = blocker.get("description", "A blocker was encountered during delivery.")
                self._merge_or_add_lesson(
                    lessons, title, description, confidence, project.id, category,
                    tags=["blocker", "delivery"]
                )

            for risk in delivery_report.risk_register:
                title = f"Risk: {risk.get('risk', 'Unknown risk')}"
                description = f"Severity: {risk.get('severity', 'UNKNOWN')}. {risk.get('risk', '')}."
                lesson_confidence = (
                    KnowledgeConfidence.EXPERIMENTAL
                    if risk.get("severity") == "CRITICAL"
                    else confidence
                )
                self._merge_or_add_lesson(
                    lessons, title, description, lesson_confidence, project.id, category,
                    tags=["risk", risk.get("severity", "").lower()]
                )

            for fw in delivery_report.failed_work:
                title = f"Execution Failure: {fw.get('title', fw.get('work_order_id', 'Unknown'))}"
                description = (
                    f"Work order {fw.get('work_order_id', '?')} failed during execution. "
                    "Investigate root cause before replicating this delivery approach."
                )
                self._merge_or_add_lesson(
                    lessons, title, description, KnowledgeConfidence.EXPERIMENTAL,
                    project.id, category, tags=["failure", "execution"]
                )

        # From failed project work orders directly
        for wo in project.work_orders:
            status_val = getattr(wo.status, "value", wo.status)
            if status_val in ("FAILED", "CANCELLED"):
                title = f"Work Order Issue: {wo.title}"
                description = (
                    f"Work order '{wo.title}' ended with status {status_val}. "
                    "Review assignment and dependencies for future similar tasks."
                )
                self._merge_or_add_lesson(
                    lessons, title, description, KnowledgeConfidence.EXPERIMENTAL,
                    project.id, category, tags=["work-order", status_val.lower()]
                )

        return list(lessons.values())

    def _extract_best_practices(
        self,
        project: Project,
        execution_reports: list[ExecutionReport] | None,
        confidence: KnowledgeConfidence,
        category: KnowledgeCategory,
    ) -> list[BestPractice]:
        practices: list[BestPractice] = []

        # From successful execution reports
        if execution_reports:
            for er in execution_reports:
                if getattr(er, "status", "") == "SUCCESS":
                    engine_name = getattr(er, "engine_name", "Unknown Engine")
                    practice = BestPractice(
                        practice_id=self._next_practice_id(),
                        title=f"Successful Execution via {engine_name}",
                        description=(
                            f"Work order {er.work_order_id} completed successfully using "
                            f"{engine_name} in {er.duration_seconds:.1f}s."
                        ),
                        applicability=(
                            f"Applicable for tasks requiring {engine_name} execution with "
                            f"similar complexity."
                        ),
                        source_project_ids=[project.id],
                        confidence=confidence,
                        tags=["execution", engine_name.lower().replace(" ", "-")],
                        category=category,
                    )
                    practices.append(practice)

        # From completed project deliverables
        completed_deliverables = [
            d for d in project.deliverables
            if getattr(getattr(d, "status", None), "value", getattr(d, "status", "")) == "APPROVED"
        ]
        if completed_deliverables:
            practice = BestPractice(
                practice_id=self._next_practice_id(),
                title=f"Deliverable Approval Workflow — {project.title}",
                description=(
                    f"{len(completed_deliverables)} deliverable(s) were approved through the "
                    "standard review-and-approval workflow."
                ),
                applicability="Applicable to projects requiring client-facing deliverable approval gates.",
                source_project_ids=[project.id],
                confidence=confidence,
                tags=["deliverable", "approval", "workflow"],
                category=category,
            )
            practices.append(practice)

        return practices

    def _extract_reusable_assets(
        self,
        project: Project,
        blueprint: SolutionBlueprint | None,
        category: KnowledgeCategory,
    ) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []

        if blueprint is not None:
            # Architecture asset
            if blueprint.recommended_solution:
                assets.append(ReusableAsset(
                    asset_id=self._next_asset_id(),
                    title=f"Architecture: {blueprint.recommended_solution.get('title', project.title)}",
                    asset_type="ARCHITECTURE",
                    content=blueprint.recommended_solution,
                    source_project_ids=[project.id],
                    description=(
                        f"Recommended solution architecture for '{project.title}'. "
                        f"Complexity: {blueprint.estimated_complexity}."
                    ),
                    tags=["architecture", blueprint.estimated_complexity.lower()],
                    category=category,
                ))

            # Workflow asset from required capabilities/skills
            if blueprint.required_capabilities or blueprint.required_skills:
                assets.append(ReusableAsset(
                    asset_id=self._next_asset_id(),
                    title=f"Capability Checklist: {project.title}",
                    asset_type="CHECKLIST",
                    content={
                        "capabilities": list(blueprint.required_capabilities),
                        "skills": list(blueprint.required_skills),
                        "departments": list(blueprint.required_departments),
                    },
                    source_project_ids=[project.id],
                    description="Reusable capability and skill checklist derived from project requirements.",
                    tags=["checklist", "capabilities", "skills"],
                    category=category,
                ))

        # Approved deliverable content as templates
        for d in project.deliverables:
            status_val = getattr(getattr(d, "status", None), "value", getattr(d, "status", ""))
            if status_val == "APPROVED" and getattr(d, "content", None):
                assets.append(ReusableAsset(
                    asset_id=self._next_asset_id(),
                    title=f"Template: {d.title}",
                    asset_type="TEMPLATE",
                    content=d.content,
                    source_project_ids=[project.id],
                    description=f"Approved deliverable template from project '{project.title}'.",
                    tags=["template", "deliverable"],
                    category=category,
                ))

        return assets

    def _extract_project_pattern(
        self,
        project: Project,
        blueprint: SolutionBlueprint | None,
        category: KnowledgeCategory,
    ) -> ProjectPattern | None:
        assigned_workers = set(
            wo.assigned_to for wo in project.work_orders if getattr(wo, "assigned_to", None)
        )
        complexity = blueprint.estimated_complexity if blueprint else "Medium"
        industry = category.value

        # Derive rough delivery phases from WO titles (first word grouping)
        phase_titles: list[str] = []
        seen: set[str] = set()
        for wo in project.work_orders:
            first_word = wo.title.split()[0] if wo.title else "Task"
            if first_word not in seen:
                seen.add(first_word)
                phase_titles.append(first_word)

        return ProjectPattern(
            pattern_id=self._next_pattern_id(),
            title=f"Delivery Pattern: {project.title}",
            description=(
                f"Delivery pattern for client '{project.client}' in the {industry} sector. "
                f"Completed with {len(project.work_orders)} work orders across "
                f"{len(assigned_workers)} assigned workers."
            ),
            industry=industry,
            complexity=complexity,
            team_size=len(assigned_workers),
            delivery_phases=phase_titles[:10],  # cap for readability
            source_project_ids=[project.id],
            tags=["pattern", project.client.lower().replace(" ", "-"), complexity.lower()],
            category=category,
        )

    def _build_case_study(
        self,
        project: Project,
        blueprint: SolutionBlueprint | None,
        delivery_report: DeliveryStatusReport | None,
    ) -> dict[str, Any]:
        completed_count = len([
            wo for wo in project.work_orders
            if getattr(getattr(wo, "status", None), "value", getattr(wo, "status", "")) == "COMPLETED"
        ])
        total_count = len(project.work_orders)
        delivery_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0.0

        return {
            "title": f"Case Study: {project.title}",
            "client": project.client,
            "challenge": project.description,
            "solution": (
                blueprint.recommended_solution.get("title", "Custom solution")
                if blueprint else "Custom solution"
            ),
            "solution_summary": (
                blueprint.executive_recommendation if blueprint else ""
            ),
            "outcome": f"Project completed with {delivery_rate}% work order completion rate.",
            "work_orders_total": total_count,
            "work_orders_completed": completed_count,
            "delivery_rate_pct": delivery_rate,
            "deliverables_approved": len([
                d for d in project.deliverables
                if getattr(getattr(d, "status", None), "value", getattr(d, "status", "")) == "APPROVED"
            ]),
            "health_at_close": delivery_report.health_status if delivery_report else "UNKNOWN",
        }

    def _build_future_recommendations(
        self,
        blueprint: SolutionBlueprint | None,
        delivery_report: DeliveryStatusReport | None,
        ceo_notes: list[str] | None,
    ) -> list[str]:
        recommendations: list[str] = []

        if blueprint:
            for risk in blueprint.risks:
                recommendations.append(f"Risk mitigation: {risk}")
            for metric in blueprint.success_metrics:
                recommendations.append(f"Track success metric in future similar projects: {metric}")

        if delivery_report:
            for item in delivery_report.ceo_attention_items:
                desc = item.get("description", "")
                if desc:
                    recommendations.append(f"Address in future projects: {desc}")

        if ceo_notes:
            for note in ceo_notes:
                if note.strip():
                    recommendations.append(f"CEO note: {note.strip()}")

        return recommendations

    # ------------------------------------------------------------------
    # Private utilities
    # ------------------------------------------------------------------

    def _merge_or_add_lesson(
        self,
        lessons: dict[str, LessonLearned],
        title: str,
        description: str,
        confidence: KnowledgeConfidence,
        project_id: str,
        category: KnowledgeCategory,
        tags: list[str] | None = None,
    ) -> None:
        """Merge duplicate lessons by title (BR-030-005)."""
        key = title.strip().lower()
        if key in lessons:
            existing = lessons[key]
            new_lesson = LessonLearned(
                lesson_id=existing.lesson_id,
                title=title,
                description=description,
                confidence=confidence,
                source_project_ids=[project_id],
                tags=tags,
                category=category,
            )
            existing.merge_sources(new_lesson)
        else:
            lessons[key] = LessonLearned(
                lesson_id=self._next_lesson_id(),
                title=title,
                description=description,
                confidence=confidence,
                source_project_ids=[project_id],
                tags=tags,
                category=category,
            )

    def _resolve_category(self, blueprint: SolutionBlueprint | None) -> KnowledgeCategory:
        if blueprint is None:
            return KnowledgeCategory.GENERAL
        # Check recommended solution and description for category hints
        all_text = " ".join([
            blueprint.client_summary,
            blueprint.business_problem,
            blueprint.executive_recommendation,
        ]).upper()
        for member in KnowledgeCategory:
            if member.value in all_text and member != KnowledgeCategory.GENERAL:
                return member
        return KnowledgeCategory.GENERAL

    def _resolve_confidence(
        self,
        delivery_report: DeliveryStatusReport | None,
        execution_reports: list[ExecutionReport] | None,
    ) -> KnowledgeConfidence:
        if delivery_report is None and not execution_reports:
            return KnowledgeConfidence.EXPERIMENTAL

        health = getattr(delivery_report, "health_status", "UNKNOWN") if delivery_report else "UNKNOWN"
        if health == "HEALTHY":
            return KnowledgeConfidence.PROVEN
        if health in ("WATCH", "AT_RISK"):
            return KnowledgeConfidence.VALIDATED
        return KnowledgeConfidence.EXPERIMENTAL

    def _next_knowledge_id(self) -> str:
        kid = f"KN-{self._knowledge_counter:06d}"
        self._knowledge_counter += 1
        return kid

    def _next_lesson_id(self) -> str:
        lid = f"LL-{self._lesson_counter:04d}"
        self._lesson_counter += 1
        return lid

    def _next_practice_id(self) -> str:
        pid = f"BP-{self._practice_counter:04d}"
        self._practice_counter += 1
        return pid

    def _next_asset_id(self) -> str:
        aid = f"RA-{self._asset_counter:04d}"
        self._asset_counter += 1
        return aid

    def _next_pattern_id(self) -> str:
        ptid = f"PT-{self._pattern_counter:04d}"
        self._pattern_counter += 1
        return ptid

    def _next_report_id(self) -> str:
        rid = f"MEM-{self._report_counter:04d}"
        self._report_counter += 1
        return rid
