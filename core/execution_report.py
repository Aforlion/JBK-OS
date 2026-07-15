from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class ExecutionReport:
    def __init__(
        self,
        report_id: str,
        work_order_id: str,
        engine_name: str,
        worker_id: str,
        status: str,
        duration_seconds: float,
        outputs: dict[str, Any],
        errors: list[str],
        created_at: str | None = None,
    ) -> None:
        self.report_id = report_id
        self.work_order_id = work_order_id
        self.engine_name = engine_name
        self.worker_id = worker_id
        self.status = status
        self.duration_seconds = duration_seconds
        self.outputs = outputs or {}
        self.errors = errors or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "work_order_id": self.work_order_id,
            "engine_name": self.engine_name,
            "worker_id": self.worker_id,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "error_count": len(self.errors),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "work_order_id": self.work_order_id,
            "engine_name": self.engine_name,
            "worker_id": self.worker_id,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "outputs": dict(self.outputs),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
