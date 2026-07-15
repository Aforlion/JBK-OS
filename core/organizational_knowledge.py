from __future__ import annotations

import logging
from enum import Enum
from typing import Any
from datetime import datetime, timezone

LOGGER = logging.getLogger(__name__)


class KnowledgeConfidence(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    PROVEN = "PROVEN"


class KnowledgeCategory(str, Enum):
    TECHNOLOGY = "TECHNOLOGY"
    EDUCATION = "EDUCATION"
    HEALTHCARE = "HEALTHCARE"
    GOVERNMENT = "GOVERNMENT"
    FINANCE = "FINANCE"
    RETAIL = "RETAIL"
    AUTOMATION = "AUTOMATION"
    AI = "AI"
    SOFTWARE = "SOFTWARE"
    MARKETING = "MARKETING"
    GENERAL = "GENERAL"

    @classmethod
    def from_string(cls, value: str) -> "KnowledgeCategory":
        normalized = (value or "").strip().upper()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.GENERAL


class LessonLearned:
    """A single lesson extracted from a completed project."""

    def __init__(
        self,
        lesson_id: str,
        title: str,
        description: str,
        confidence: KnowledgeConfidence | str,
        source_project_ids: list[str],
        tags: list[str] | None = None,
        category: KnowledgeCategory | str = KnowledgeCategory.GENERAL,
        created_at: str | None = None,
    ) -> None:
        if not lesson_id:
            raise ValueError("Lesson ID is required.")
        if not title:
            raise ValueError("Lesson title is required.")
        if not description:
            raise ValueError("Lesson description is required.")
        if not source_project_ids:
            raise ValueError("At least one source project ID is required.")

        self.lesson_id = lesson_id
        self.title = title
        self.description = description
        self.confidence = (
            confidence
            if isinstance(confidence, KnowledgeConfidence)
            else KnowledgeConfidence(confidence)
        )
        self.source_project_ids = list(source_project_ids)
        self.tags = [t.strip() for t in tags] if tags else []
        self.category = (
            category
            if isinstance(category, KnowledgeCategory)
            else KnowledgeCategory.from_string(str(category))
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def merge_sources(self, other: "LessonLearned") -> None:
        """Merge source project IDs from another lesson with same title (BR-030-005)."""
        for pid in other.source_project_ids:
            if pid not in self.source_project_ids:
                self.source_project_ids.append(pid)
        # Upgrade confidence if other is more proven
        confidence_rank = {
            KnowledgeConfidence.EXPERIMENTAL: 0,
            KnowledgeConfidence.VALIDATED: 1,
            KnowledgeConfidence.PROVEN: 2,
        }
        if confidence_rank.get(other.confidence, 0) > confidence_rank.get(self.confidence, 0):
            self.confidence = other.confidence

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.category.value.lower()
            or any(q in t.lower() for t in self.tags)
            or any(q in pid.lower() for pid in self.source_project_ids)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "title": self.title,
            "confidence": self.confidence.value,
            "category": self.category.value,
            "source_project_count": len(self.source_project_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence.value,
            "source_project_ids": list(self.source_project_ids),
            "tags": list(self.tags),
            "category": self.category.value,
            "created_at": self.created_at,
        }


class BestPractice:
    """A proven approach or reusable methodology extracted from a project."""

    def __init__(
        self,
        practice_id: str,
        title: str,
        description: str,
        applicability: str,
        source_project_ids: list[str],
        confidence: KnowledgeConfidence | str = KnowledgeConfidence.VALIDATED,
        tags: list[str] | None = None,
        category: KnowledgeCategory | str = KnowledgeCategory.GENERAL,
        created_at: str | None = None,
    ) -> None:
        if not practice_id:
            raise ValueError("Practice ID is required.")
        if not title:
            raise ValueError("Best practice title is required.")
        if not source_project_ids:
            raise ValueError("At least one source project ID is required.")

        self.practice_id = practice_id
        self.title = title
        self.description = description or ""
        self.applicability = applicability or ""
        self.source_project_ids = list(source_project_ids)
        self.confidence = (
            confidence
            if isinstance(confidence, KnowledgeConfidence)
            else KnowledgeConfidence(confidence)
        )
        self.tags = [t.strip() for t in tags] if tags else []
        self.category = (
            category
            if isinstance(category, KnowledgeCategory)
            else KnowledgeCategory.from_string(str(category))
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.applicability.lower()
            or q in self.category.value.lower()
            or any(q in t.lower() for t in self.tags)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "title": self.title,
            "confidence": self.confidence.value,
            "category": self.category.value,
            "source_project_count": len(self.source_project_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "title": self.title,
            "description": self.description,
            "applicability": self.applicability,
            "source_project_ids": list(self.source_project_ids),
            "confidence": self.confidence.value,
            "tags": list(self.tags),
            "category": self.category.value,
            "created_at": self.created_at,
        }


class ReusableAsset:
    """A concrete reusable artifact extracted from a project (template, prompt, code, workflow, architecture)."""

    ASSET_TYPES = frozenset({
        "TEMPLATE", "PROMPT", "CODE", "WORKFLOW", "ARCHITECTURE", "PLAYBOOK", "CHECKLIST", "GENERAL"
    })

    def __init__(
        self,
        asset_id: str,
        title: str,
        asset_type: str,
        content: Any,
        source_project_ids: list[str],
        description: str = "",
        tags: list[str] | None = None,
        category: KnowledgeCategory | str = KnowledgeCategory.GENERAL,
        created_at: str | None = None,
    ) -> None:
        if not asset_id:
            raise ValueError("Asset ID is required.")
        if not title:
            raise ValueError("Asset title is required.")
        if not source_project_ids:
            raise ValueError("At least one source project ID is required.")

        normalized_type = (asset_type or "GENERAL").strip().upper()
        if normalized_type not in self.ASSET_TYPES:
            normalized_type = "GENERAL"

        self.asset_id = asset_id
        self.title = title
        self.asset_type = normalized_type
        self.content = content
        self.source_project_ids = list(source_project_ids)
        self.description = description or ""
        self.tags = [t.strip() for t in tags] if tags else []
        self.category = (
            category
            if isinstance(category, KnowledgeCategory)
            else KnowledgeCategory.from_string(str(category))
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        content_str = str(self.content).lower() if self.content else ""
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.asset_type.lower()
            or q in self.category.value.lower()
            or q in content_str
            or any(q in t.lower() for t in self.tags)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "title": self.title,
            "asset_type": self.asset_type,
            "category": self.category.value,
            "source_project_count": len(self.source_project_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "title": self.title,
            "asset_type": self.asset_type,
            "content": self.content,
            "source_project_ids": list(self.source_project_ids),
            "description": self.description,
            "tags": list(self.tags),
            "category": self.category.value,
            "created_at": self.created_at,
        }


class ProjectPattern:
    """A recurring structural or behavioural pattern detected across one or more projects."""

    def __init__(
        self,
        pattern_id: str,
        title: str,
        description: str,
        industry: str,
        complexity: str,
        team_size: int,
        delivery_phases: list[str],
        source_project_ids: list[str],
        tags: list[str] | None = None,
        category: KnowledgeCategory | str = KnowledgeCategory.GENERAL,
        created_at: str | None = None,
    ) -> None:
        if not pattern_id:
            raise ValueError("Pattern ID is required.")
        if not title:
            raise ValueError("Pattern title is required.")
        if not source_project_ids:
            raise ValueError("At least one source project ID is required.")

        self.pattern_id = pattern_id
        self.title = title
        self.description = description or ""
        self.industry = industry or "General"
        self.complexity = complexity or "Medium"
        self.team_size = int(team_size or 0)
        self.delivery_phases = list(delivery_phases or [])
        self.source_project_ids = list(source_project_ids)
        self.tags = [t.strip() for t in tags] if tags else []
        self.category = (
            category
            if isinstance(category, KnowledgeCategory)
            else KnowledgeCategory.from_string(str(category))
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def matches(self, query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.industry.lower()
            or q in self.complexity.lower()
            or q in self.category.value.lower()
            or any(q in p.lower() for p in self.delivery_phases)
            or any(q in t.lower() for t in self.tags)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "title": self.title,
            "industry": self.industry,
            "complexity": self.complexity,
            "team_size": self.team_size,
            "source_project_count": len(self.source_project_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "title": self.title,
            "description": self.description,
            "industry": self.industry,
            "complexity": self.complexity,
            "team_size": self.team_size,
            "delivery_phases": list(self.delivery_phases),
            "source_project_ids": list(self.source_project_ids),
            "tags": list(self.tags),
            "category": self.category.value,
            "created_at": self.created_at,
        }


class OrganizationalKnowledge:
    """Top-level knowledge record tying together all knowledge objects from a completed project.

    ID format: KN-000001 (BR-030-003)
    """

    def __init__(
        self,
        knowledge_id: str,
        title: str,
        category: KnowledgeCategory | str,
        source_project_ids: list[str],
        lessons_learned: list[LessonLearned] | None = None,
        best_practices: list[BestPractice] | None = None,
        reusable_assets: list[ReusableAsset] | None = None,
        patterns: list[ProjectPattern] | None = None,
        case_study: dict[str, Any] | None = None,
        future_recommendations: list[str] | None = None,
        tags: list[str] | None = None,
        description: str = "",
        created_at: str | None = None,
    ) -> None:
        if not knowledge_id:
            raise ValueError("Knowledge ID is required.")
        if not title:
            raise ValueError("Organizational knowledge title is required.")
        if not source_project_ids:
            raise ValueError("At least one source project ID is required (BR-030-007).")

        self.knowledge_id = knowledge_id
        self.title = title
        self.category = (
            category
            if isinstance(category, KnowledgeCategory)
            else KnowledgeCategory.from_string(str(category))
        )
        self.source_project_ids = list(source_project_ids)
        self.lessons_learned = list(lessons_learned or [])
        self.best_practices = list(best_practices or [])
        self.reusable_assets = list(reusable_assets or [])
        self.patterns = list(patterns or [])
        self.case_study = dict(case_study or {})
        self.future_recommendations = list(future_recommendations or [])
        self.tags = [t.strip() for t in tags] if tags else []
        self.description = description or ""
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @property
    def id(self) -> str:
        return self.knowledge_id

    def matches(self, query: str) -> bool:
        """Keyword search across all text fields (BR-030-009)."""
        if not query:
            return False
        q = query.strip().lower()
        if (
            q in self.title.lower()
            or q in self.description.lower()
            or q in self.category.value.lower()
            or any(q in t.lower() for t in self.tags)
            or any(q in pid.lower() for pid in self.source_project_ids)
            or any(q in r.lower() for r in self.future_recommendations)
        ):
            return True
        for ll in self.lessons_learned:
            if ll.matches(q):
                return True
        for bp in self.best_practices:
            if bp.matches(q):
                return True
        for ra in self.reusable_assets:
            if ra.matches(q):
                return True
        for pt in self.patterns:
            if pt.matches(q):
                return True
        return False

    def summary(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "category": self.category.value,
            "source_project_count": len(self.source_project_ids),
            "lesson_count": len(self.lessons_learned),
            "best_practice_count": len(self.best_practices),
            "reusable_asset_count": len(self.reusable_assets),
            "pattern_count": len(self.patterns),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "category": self.category.value,
            "source_project_ids": list(self.source_project_ids),
            "description": self.description,
            "tags": list(self.tags),
            "lessons_learned": [ll.to_dict() for ll in self.lessons_learned],
            "best_practices": [bp.to_dict() for bp in self.best_practices],
            "reusable_assets": [ra.to_dict() for ra in self.reusable_assets],
            "patterns": [pt.to_dict() for pt in self.patterns],
            "case_study": dict(self.case_study),
            "future_recommendations": list(self.future_recommendations),
            "created_at": self.created_at,
        }
