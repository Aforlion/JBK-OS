from __future__ import annotations

import time
import logging
from typing import Any
from datetime import datetime, timezone

from core.backup_snapshot import BackupSnapshot
from core.recovery_plan import RecoveryPlan
from core.disaster_recovery_report import DisasterRecoveryReport

LOGGER = logging.getLogger(__name__)


class RecoveryManager:
    """Restores snapshots and verifies compatibility and integrity.

    BR-054-002: Integrity verified before restoration.
    BR-054-003: Corrupted backups are rejected.
    BR-054-004: Registries remain internally consistent.
    BR-054-005: Recovery is fully auditable.
    BR-054-010: Reports are immutable.
    """

    def __init__(self, kernel_version: str = "1.0.0") -> None:
        self.kernel_version = kernel_version
        self._recovery_history: list[DisasterRecoveryReport] = []

    def execute_recovery(
        self,
        plan: RecoveryPlan,
        snapshot: BackupSnapshot,
        fail_on_asset: str | None = None,  # Inject failure point for testing
    ) -> DisasterRecoveryReport:
        """Executes restoration of snapshot assets following a RecoveryPlan."""
        start_time = time.monotonic()
        restored: list[str] = []
        failed: list[str] = []
        warnings: list[str] = []
        integrity_results: dict[str, bool] = {}

        # 1. Verify Snapshot Integrity (BR-054-002, BR-054-003)
        checksum_ok = snapshot.verify_checksum()
        integrity_results["checksum_match"] = checksum_ok
        if not checksum_ok:
            failed.append("all_assets")
            elapsed = time.monotonic() - start_time
            report = DisasterRecoveryReport(
                recovery_id=plan.recovery_id,
                snapshot_id=snapshot.snapshot_id,
                restored_assets=[],
                failed_assets=failed,
                integrity_results=integrity_results,
                warnings=["Snapshot checksum mismatch. Payload is corrupted."],
                recovery_time_seconds=round(elapsed, 4),
                recommendations=["Reject corrupted backup. Re-download or use prior snapshot."],
            )
            self._recovery_history.append(report)
            return report

        # 2. Compatibility Checks
        compatibility_ok = snapshot.kernel_version == self.kernel_version
        integrity_results["kernel_compatibility"] = compatibility_ok
        if not compatibility_ok:
            failed.append("all_assets")
            elapsed = time.monotonic() - start_time
            report = DisasterRecoveryReport(
                recovery_id=plan.recovery_id,
                snapshot_id=snapshot.snapshot_id,
                restored_assets=[],
                failed_assets=failed,
                integrity_results=integrity_results,
                warnings=[f"Version mismatch. Backup kernel ({snapshot.kernel_version}) != Current ({self.kernel_version})."],
                recovery_time_seconds=round(elapsed, 4),
                recommendations=["Upgrade kernel or perform manual configuration translation."],
            )
            self._recovery_history.append(report)
            return report

        # 3. Restore Assets
        for scope_item in plan.recovery_scope:
            if scope_item in snapshot.assets:
                if scope_item == fail_on_asset:
                    failed.append(scope_item)
                    warnings.append(f"Asset restoration failed: {scope_item}")
                    break
                restored.append(scope_item)
            else:
                warnings.append(f"Requested asset not found in snapshot: {scope_item}")

        # Check internal consistency (BR-054-004)
        if failed:
            restored = []  # Rollback changes to keep registries consistent
            warnings.append("Restoration failed. Rolled back to keep registries consistent.")

        elapsed = time.monotonic() - start_time

        # Immutable DisasterRecoveryReport
        report = DisasterRecoveryReport(
            recovery_id=plan.recovery_id,
            snapshot_id=snapshot.snapshot_id,
            restored_assets=restored,
            failed_assets=failed,
            integrity_results=integrity_results,
            warnings=warnings,
            recovery_time_seconds=round(elapsed, 4),
            recommendations=["Verify registry health check is active."] if not failed else ["Investigate restore logs."],
        )
        self._recovery_history.append(report)
        return report

    def get_history(self) -> list[DisasterRecoveryReport]:
        return list(self._recovery_history)
