from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DisasterRecoveryReport:
    """Immutable summary of a completed recovery operation.

    BR-054-010: Backup and recovery reports are immutable.
    BR-054-005: Recovery is fully auditable.
    """

    _FROZEN = False

    def __init__(
        self,
        recovery_id: str,
        snapshot_id: str,
        restored_assets: list[str],
        failed_assets: list[str],
        integrity_results: dict[str, bool],
        warnings: list[str],
        recovery_time_seconds: float,
        recommendations: list[str] | None = None,
        generated_at: str | None = None,
    ) -> None:
        self.recovery_id = recovery_id
        self.snapshot_id = snapshot_id
        self.restored_assets = restored_assets
        self.failed_assets = failed_assets
        self.integrity_results = integrity_results
        self.warnings = warnings
        self.recovery_time_seconds = recovery_time_seconds
        self.recommendations = recommendations or []
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self._FROZEN = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_FROZEN", False):
            raise AttributeError(f"DisasterRecoveryReport is immutable. Cannot set '{name}'.")
        super().__setattr__(name, value)

    @property
    def success(self) -> bool:
        return len(self.failed_assets) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "snapshot_id": self.snapshot_id,
            "restored_assets": self.restored_assets,
            "failed_assets": self.failed_assets,
            "integrity_results": self.integrity_results,
            "warnings": self.warnings,
            "recovery_time_seconds": self.recovery_time_seconds,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
            "success": self.success,
        }
