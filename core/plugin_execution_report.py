from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class PluginExecutionReport:
    """Immutable record of a single plugin execution (BR-053-007).

    BR-053-008: Serializable.
    """

    _FROZEN = False

    def __init__(
        self,
        execution_id: str,
        plugin_id: str,
        capability_id: str,
        execution_time_ms: float,
        status: str,          # SUCCESS, FAILED, SKIPPED
        outputs: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
        generated_at: str | None = None,
    ) -> None:
        self.execution_id = execution_id
        self.plugin_id = plugin_id
        self.capability_id = capability_id
        self.execution_time_ms = execution_time_ms
        self.status = status
        self.outputs = outputs or {}
        self.warnings = warnings or []
        self.errors = errors or []
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self._FROZEN = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_FROZEN", False):
            raise AttributeError(f"PluginExecutionReport is immutable. Cannot set '{name}'.")
        super().__setattr__(name, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "plugin_id": self.plugin_id,
            "capability_id": self.capability_id,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "outputs": self.outputs,
            "warnings": self.warnings,
            "errors": self.errors,
            "generated_at": self.generated_at,
        }
