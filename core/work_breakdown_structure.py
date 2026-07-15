from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class WorkBreakdownStructure:
    def __init__(
        self,
        wbs_id: str,
        project_id: str,
        delivery_plan_id: str,
        tasks: list[dict[str, Any]],
        created_at: str | None = None,
    ) -> None:
        self.wbs_id = wbs_id
        self.project_id = project_id
        self.delivery_plan_id = delivery_plan_id
        self.tasks = tasks or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        total_effort = sum(task.get("estimated_effort_hours", 0.0) for task in self.tasks)
        return {
            "wbs_id": self.wbs_id,
            "project_id": self.project_id,
            "delivery_plan_id": self.delivery_plan_id,
            "task_count": len(self.tasks),
            "total_estimated_effort_hours": total_effort,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "wbs_id": self.wbs_id,
            "project_id": self.project_id,
            "delivery_plan_id": self.delivery_plan_id,
            "tasks": [dict(t) for t in self.tasks],
            "created_at": self.created_at,
        }
