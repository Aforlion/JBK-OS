from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DeliveryPlan:
    def __init__(
        self,
        delivery_plan_id: str,
        project_id: str,
        phases: list[dict[str, Any]],
        work_streams: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
        created_at: str | None = None,
    ) -> None:
        self.delivery_plan_id = delivery_plan_id
        self.project_id = project_id
        self.phases = phases or []
        self.work_streams = work_streams or []
        self.dependencies = dependencies or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "delivery_plan_id": self.delivery_plan_id,
            "project_id": self.project_id,
            "phase_count": len(self.phases),
            "work_stream_count": len(self.work_streams),
            "dependency_count": len(self.dependencies),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_plan_id": self.delivery_plan_id,
            "project_id": self.project_id,
            "phases": [dict(p) for p in self.phases],
            "work_streams": [dict(w) for w in self.work_streams],
            "dependencies": [dict(d) for d in self.dependencies],
            "created_at": self.created_at,
        }
