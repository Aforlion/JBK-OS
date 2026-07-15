from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone


class ImprovementPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_confidence(cls, confidence_str: str) -> "ImprovementPriority":
        mapping = {
            "EXPERIMENTAL": cls.LOW,
            "VALIDATED": cls.MEDIUM,
            "PROVEN": cls.HIGH,
        }
        return mapping.get((confidence_str or "").upper(), cls.MEDIUM)


class ImprovementCategory(str, Enum):
    PROCESS = "PROCESS"
    TECHNOLOGY = "TECHNOLOGY"
    ARCHITECTURE = "ARCHITECTURE"
    OPERATIONS = "OPERATIONS"
    SECURITY = "SECURITY"
    SALES = "SALES"
    MARKETING = "MARKETING"
    FINANCE = "FINANCE"
    HR = "HR"
    KNOWLEDGE = "KNOWLEDGE"
    TRAINING = "TRAINING"
    GENERAL = "GENERAL"

    @classmethod
    def from_string(cls, value: str) -> "ImprovementCategory":
        normalized = (value or "").strip().upper()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.GENERAL


class ContinuousImprovementRecommendation:
    """A single actionable improvement recommendation backed by evidence.

    BR-031-001: Must be evidence-based (min 1 source knowledge asset unless CRITICAL).
    BR-031-003: Must include supporting evidence with source references.
    BR-031-004: Must include confidence level.
    BR-031-005: Must be categorized.
    BR-031-008: Must be traceable to source knowledge.
    """

    def __init__(
        self,
        recommendation_id: str,
        title: str,
        description: str,
        category: ImprovementCategory | str,
        priority: ImprovementPriority | str,
        confidence: str,
        evidence: list[dict[str, Any]],
        source_knowledge_ids: list[str],
        source_project_ids: list[str],
        action_items: list[str] | None = None,
        tags: list[str] | None = None,
        is_critical_single_event: bool = False,
        created_at: str | None = None,
    ) -> None:
        if not recommendation_id:
            raise ValueError("Recommendation ID is required.")
        if not title:
            raise ValueError("Recommendation title is required.")
        if not description:
            raise ValueError("Recommendation description is required.")
        # BR-031-001: evidence required unless flagged critical single event
        if not evidence and not is_critical_single_event:
            raise ValueError(
                "At least one evidence item is required (BR-031-001). "
                "Set is_critical_single_event=True to bypass for single critical events."
            )
        # BR-031-008: must reference source knowledge
        if not source_knowledge_ids:
            raise ValueError("At least one source knowledge ID is required (BR-031-008).")

        self.recommendation_id = recommendation_id
        self.title = title
        self.description = description
        self.category = (
            category
            if isinstance(category, ImprovementCategory)
            else ImprovementCategory.from_string(str(category))
        )
        self.priority = (
            priority
            if isinstance(priority, ImprovementPriority)
            else ImprovementPriority(priority)
        )
        self.confidence = (confidence or "MEDIUM").upper()
        self.evidence = list(evidence or [])
        self.source_knowledge_ids = list(source_knowledge_ids)
        self.source_project_ids = list(source_project_ids or [])
        self.action_items = list(action_items or [])
        self.tags = [t.strip() for t in tags] if tags else []
        self.is_critical_single_event = is_critical_single_event
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.category.value.lower()
            or q in self.priority.value.lower()
            or any(q in t.lower() for t in self.tags)
            or any(q in kid.lower() for kid in self.source_knowledge_ids)
            or any(q in pid.lower() for pid in self.source_project_ids)
            or any(q in str(e).lower() for e in self.evidence)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "category": self.category.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "evidence_count": len(self.evidence),
            "source_knowledge_count": len(self.source_knowledge_ids),
            "source_project_count": len(self.source_project_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "source_knowledge_ids": list(self.source_knowledge_ids),
            "source_project_ids": list(self.source_project_ids),
            "action_items": list(self.action_items),
            "tags": list(self.tags),
            "is_critical_single_event": self.is_critical_single_event,
            "created_at": self.created_at,
        }


class ContinuousImprovementReport:
    """Output report produced by the Continuous Improvement Engine.

    BR-031-009: Must serialize completely.
    BR-031-006: Never modifies company documents.
    BR-031-007: Recommendations require executive approval before becoming standards.
    """

    def __init__(
        self,
        report_id: str,
        knowledge_assets_analyzed: int,
        lessons_analyzed: int,
        recommendations: list[ContinuousImprovementRecommendation],
        recurring_problems: list[dict[str, Any]],
        recurring_successes: list[dict[str, Any]],
        standards_to_update: list[dict[str, Any]],
        sop_recommendations: list[dict[str, Any]],
        template_recommendations: list[dict[str, Any]],
        specification_recommendations: list[dict[str, Any]],
        skill_recommendations: list[dict[str, Any]],
        warnings: list[str],
        created_at: str | None = None,
    ) -> None:
        if not report_id:
            raise ValueError("Report ID is required.")

        self.report_id = report_id
        self.knowledge_assets_analyzed = int(knowledge_assets_analyzed or 0)
        self.lessons_analyzed = int(lessons_analyzed or 0)
        self.recommendations = list(recommendations or [])
        self.recurring_problems = list(recurring_problems or [])
        self.recurring_successes = list(recurring_successes or [])
        self.standards_to_update = list(standards_to_update or [])
        self.sop_recommendations = list(sop_recommendations or [])
        self.template_recommendations = list(template_recommendations or [])
        self.specification_recommendations = list(specification_recommendations or [])
        self.skill_recommendations = list(skill_recommendations or [])
        self.warnings = list(warnings or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @property
    def high_priority_count(self) -> int:
        return sum(
            1 for r in self.recommendations
            if r.priority in (ImprovementPriority.HIGH, ImprovementPriority.CRITICAL)
        )

    @property
    def by_category(self) -> dict[str, list[ContinuousImprovementRecommendation]]:
        result: dict[str, list[ContinuousImprovementRecommendation]] = {}
        for rec in self.recommendations:
            key = rec.category.value
            result.setdefault(key, []).append(rec)
        return result

    def summary(self) -> dict[str, Any]:
        category_counts: dict[str, int] = {}
        priority_counts: dict[str, int] = {}
        for rec in self.recommendations:
            category_counts[rec.category.value] = category_counts.get(rec.category.value, 0) + 1
            priority_counts[rec.priority.value] = priority_counts.get(rec.priority.value, 0) + 1

        return {
            "report_id": self.report_id,
            "knowledge_assets_analyzed": self.knowledge_assets_analyzed,
            "lessons_analyzed": self.lessons_analyzed,
            "total_recommendations": len(self.recommendations),
            "high_priority_count": self.high_priority_count,
            "recurring_problems": len(self.recurring_problems),
            "recurring_successes": len(self.recurring_successes),
            "standards_to_update": len(self.standards_to_update),
            "sop_recommendations": len(self.sop_recommendations),
            "template_recommendations": len(self.template_recommendations),
            "specification_recommendations": len(self.specification_recommendations),
            "skill_recommendations": len(self.skill_recommendations),
            "by_category": category_counts,
            "by_priority": priority_counts,
            "warning_count": len(self.warnings),
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "knowledge_assets_analyzed": self.knowledge_assets_analyzed,
            "lessons_analyzed": self.lessons_analyzed,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "recurring_problems": list(self.recurring_problems),
            "recurring_successes": list(self.recurring_successes),
            "standards_to_update": list(self.standards_to_update),
            "sop_recommendations": list(self.sop_recommendations),
            "template_recommendations": list(self.template_recommendations),
            "specification_recommendations": list(self.specification_recommendations),
            "skill_recommendations": list(self.skill_recommendations),
            "warnings": list(self.warnings),
            "summary": self.summary(),
            "created_at": self.created_at,
        }
