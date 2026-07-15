from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.organizational_knowledge import OrganizationalKnowledge


class OrganizationalMemoryReport:
    """Output report produced by the Organizational Memory Engine after archiving a project."""

    def __init__(
        self,
        report_id: str,
        project_id: str,
        knowledge_assets: list[OrganizationalKnowledge],
        case_study: dict[str, Any],
        future_recommendations: list[str],
        warnings: list[str],
        created_at: str | None = None,
    ) -> None:
        if not report_id:
            raise ValueError("Report ID is required.")
        if not project_id:
            raise ValueError("Project ID is required.")

        self.report_id = report_id
        self.project_id = project_id
        self.knowledge_assets = list(knowledge_assets or [])
        self.case_study = dict(case_study or {})
        self.future_recommendations = list(future_recommendations or [])
        self.warnings = list(warnings or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @property
    def total_lessons_learned(self) -> int:
        return sum(len(ka.lessons_learned) for ka in self.knowledge_assets)

    @property
    def total_best_practices(self) -> int:
        return sum(len(ka.best_practices) for ka in self.knowledge_assets)

    @property
    def total_reusable_assets(self) -> int:
        return sum(len(ka.reusable_assets) for ka in self.knowledge_assets)

    @property
    def total_patterns(self) -> int:
        return sum(len(ka.patterns) for ka in self.knowledge_assets)

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "knowledge_asset_count": len(self.knowledge_assets),
            "total_lessons_learned": self.total_lessons_learned,
            "total_best_practices": self.total_best_practices,
            "total_reusable_assets": self.total_reusable_assets,
            "total_patterns": self.total_patterns,
            "warning_count": len(self.warnings),
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "knowledge_assets": [ka.to_dict() for ka in self.knowledge_assets],
            "case_study": dict(self.case_study),
            "future_recommendations": list(self.future_recommendations),
            "warnings": list(self.warnings),
            "summary": self.summary(),
            "created_at": self.created_at,
        }
