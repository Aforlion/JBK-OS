from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class AIUsageRecord:
    """Tracks operational metrics for every AI request (BR-037-008)."""

    def __init__(
        self,
        record_id: str,
        request_id: str,
        provider_id: str,
        model: str,
        latency_ms: int,
        token_usage: dict[str, int],
        estimated_cost: float,
        success: bool,
        timestamp: str | None = None,
    ) -> None:
        if not record_id:
            raise ValueError("Record ID is required.")
        if not request_id:
            raise ValueError("Request ID is required.")
        if not provider_id:
            raise ValueError("Provider ID is required.")

        self.record_id = record_id
        self.request_id = request_id
        self.provider_id = provider_id
        self.model = model
        self.latency_ms = latency_ms
        self.token_usage = dict(token_usage or {})
        self.estimated_cost = estimated_cost
        self.success = success
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "success": self.success,
            "estimated_cost": self.estimated_cost,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "token_usage": dict(self.token_usage),
            "estimated_cost": self.estimated_cost,
            "success": self.success,
            "timestamp": self.timestamp,
        }
