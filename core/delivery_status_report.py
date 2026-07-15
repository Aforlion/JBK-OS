from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DeliveryStatusReport:
    def __init__(
        self,
        report_id: str,
        project_id: str,
        health_status: str,
        active_work: list[dict[str, Any]],
        waiting_work: list[dict[str, Any]],
        completed_work: list[dict[str, Any]],
        failed_work: list[dict[str, Any]],
        risk_register: list[dict[str, Any]],
        worker_utilization: dict[str, Any],
        blockers: list[dict[str, Any]],
        ceo_attention_items: list[dict[str, Any]],
        corrective_recommendations: list[dict[str, Any]],
        created_at: str | None = None,
    ) -> None:
        self.report_id = report_id
        self.project_id = project_id
        self.health_status = health_status
        self.active_work = active_work or []
        self.waiting_work = waiting_work or []
        self.completed_work = completed_work or []
        self.failed_work = failed_work or []
        self.risk_register = risk_register or []
        self.worker_utilization = worker_utilization or {}
        self.blockers = blockers or []
        self.ceo_attention_items = ceo_attention_items or []
        self.corrective_recommendations = corrective_recommendations or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "health_status": self.health_status,
            "active_count": len(self.active_work),
            "waiting_count": len(self.waiting_work),
            "completed_count": len(self.completed_work),
            "failed_count": len(self.failed_work),
            "blocker_count": len(self.blockers),
            "ceo_attention_count": len(self.ceo_attention_items),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "health_status": self.health_status,
            "active_work": [dict(aw) for aw in self.active_work],
            "waiting_work": [dict(ww) for ww in self.waiting_work],
            "completed_work": [dict(cw) for cw in self.completed_work],
            "failed_work": [dict(fw) for fw in self.failed_work],
            "risk_register": [dict(rr) for rr in self.risk_register],
            "worker_utilization": dict(self.worker_utilization),
            "blockers": [dict(b) for b in self.blockers],
            "ceo_attention_items": [dict(c) for c in self.ceo_attention_items],
            "corrective_recommendations": [dict(cr) for cr in self.corrective_recommendations],
            "created_at": self.created_at,
        }
