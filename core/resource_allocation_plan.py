from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class ResourceAllocationPlan:
    def __init__(
        self,
        allocation_id: str,
        project_id: str,
        assignments: list[dict[str, Any]],
        unassigned_tasks: list[dict[str, Any]],
        workload_summary: dict[str, Any],
        utilization: dict[str, Any],
        warnings: list[str],
        created_at: str | None = None,
    ) -> None:
        self.allocation_id = allocation_id
        self.project_id = project_id
        self.assignments = assignments or []
        self.unassigned_tasks = unassigned_tasks or []
        self.workload_summary = workload_summary or {}
        self.utilization = utilization or {}
        self.warnings = warnings or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "project_id": self.project_id,
            "assigned_task_count": len(self.assignments),
            "unassigned_task_count": len(self.unassigned_tasks),
            "warning_count": len(self.warnings),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "project_id": self.project_id,
            "assignments": [dict(a) for a in self.assignments],
            "unassigned_tasks": [dict(ut) for ut in self.unassigned_tasks],
            "workload_summary": dict(self.workload_summary),
            "utilization": dict(self.utilization),
            "warnings": list(self.warnings),
            "created_at": self.created_at,
        }
