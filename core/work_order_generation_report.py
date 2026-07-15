from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class WorkOrderGenerationReport:
    def __init__(
        self,
        generation_id: str,
        project_id: str,
        created_work_orders: list[dict[str, Any]],
        skipped_tasks: list[dict[str, Any]],
        dependency_graph: dict[str, list[str]],
        warnings: list[str],
        summary: dict[str, Any],
        created_at: str | None = None,
    ) -> None:
        self.generation_id = generation_id
        self.project_id = project_id
        self.created_work_orders = created_work_orders or []
        self.skipped_tasks = skipped_tasks or []
        self.dependency_graph = dependency_graph or {}
        self.warnings = warnings or []
        self.generation_summary = summary or {}
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "project_id": self.project_id,
            "created_work_orders_count": len(self.created_work_orders),
            "skipped_tasks_count": len(self.skipped_tasks),
            "warning_count": len(self.warnings),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "project_id": self.project_id,
            "created_work_orders": [dict(wo) for wo in self.created_work_orders],
            "skipped_tasks": [dict(st) for st in self.skipped_tasks],
            "dependency_graph": dict(self.dependency_graph),
            "warnings": list(self.warnings),
            "summary": dict(self.generation_summary),
            "created_at": self.created_at,
        }
