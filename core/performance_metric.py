from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class PerformanceMetric:
    """Tracks performance and resource usage metrics of system engines.

    BR-050-006: Fully serializable to dictionary format.
    """

    def __init__(
        self,
        engine_name: str,
        execution_time_ms: float,
        cpu_time: float = 0.0,
        memory_usage: float = 0.0,
        ai_tokens: int = 0,
        ai_cost: float = 0.0,
        success: bool = True,
        retries: int = 0,
        timestamp: str | None = None,
    ) -> None:
        self.engine_name = engine_name
        self.execution_time_ms = execution_time_ms
        self.cpu_time = cpu_time
        self.memory_usage = memory_usage
        self.ai_tokens = ai_tokens
        self.ai_cost = ai_cost
        self.success = success
        self.retries = retries
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_name": self.engine_name,
            "execution_time_ms": self.execution_time_ms,
            "cpu_time": self.cpu_time,
            "memory_usage": self.memory_usage,
            "ai_tokens": self.ai_tokens,
            "ai_cost": self.ai_cost,
            "success": self.success,
            "retries": self.retries,
            "timestamp": self.timestamp,
        }
