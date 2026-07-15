from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.backup_snapshot import BackupSnapshot, BACKUP_TYPES

LOGGER = logging.getLogger(__name__)

# Retention limits (number of snapshots to keep per policy)
RETENTION_LIMITS: dict[str, int] = {
    "DAILY": 7,
    "WEEKLY": 4,
    "MONTHLY": 12,
    "MANUAL": 999,
}


class BackupManager:
    """Creates, validates, archives, and prunes backups.

    BR-054-001: Backups never modify business data.
    BR-054-006: Retention policies are configurable.
    BR-054-008: Configuration and operational data backed up separately.
    BR-054-009: Business engines remain unaware of backup operations.
    """

    def __init__(self, kernel_version: str = "1.0.0") -> None:
        self.kernel_version = kernel_version
        self._snapshots: dict[str, BackupSnapshot] = {}
        self._counter = 1

    # ------------------------------------------------------------------
    # Create Backups
    # ------------------------------------------------------------------

    def create_snapshot(
        self,
        backup_type: str,
        assets: dict[str, Any],
        retention_policy: str = "DAILY",
    ) -> BackupSnapshot:
        """Create and checksum a new snapshot.

        BR-054-001: Never mutates the assets dict — works from a shallow copy.
        """
        snap_id = f"SNAP-{self._counter:04d}"
        self._counter += 1

        snapshot = BackupSnapshot(
            snapshot_id=snap_id,
            backup_type=backup_type,
            kernel_version=self.kernel_version,
            assets=dict(assets),          # shallow copy — never mutates business data
            status="IN_PROGRESS",
            retention_policy=retention_policy,
        )
        snapshot.compute_checksum()
        snapshot.status = "COMPLETED"
        self._snapshots[snap_id] = snapshot

        LOGGER.info("backup_manager snapshot_id=%s type=%s assets=%d status=COMPLETED",
                    snap_id, backup_type, snapshot.asset_count)
        return snapshot

    def create_incremental_snapshot(
        self,
        base_snapshot_id: str,
        changed_assets: dict[str, Any],
        retention_policy: str = "DAILY",
    ) -> BackupSnapshot:
        """Create an incremental backup relative to a base snapshot."""
        base = self._snapshots.get(base_snapshot_id)
        if not base:
            raise KeyError(f"Base snapshot '{base_snapshot_id}' not found.")

        merged = dict(base.assets)
        merged.update(changed_assets)

        return self.create_snapshot("INCREMENTAL", merged, retention_policy)

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify snapshot checksum (BR-054-002)."""
        snapshot = self._get_or_raise(snapshot_id)
        return snapshot.verify_checksum()

    def corrupt_snapshot(self, snapshot_id: str) -> None:
        """Test-only helper to simulate corruption (BR-054-003)."""
        snapshot = self._get_or_raise(snapshot_id)
        snapshot.assets["__corrupted__"] = True      # tamper payload
        snapshot.validation_status = "CORRUPTED"
        snapshot.status = "CORRUPTED"

    # ------------------------------------------------------------------
    # Retention (BR-054-006)
    # ------------------------------------------------------------------

    def apply_retention_policy(self, policy: str = "DAILY") -> list[str]:
        """Remove oldest snapshots beyond the retention limit. Returns pruned IDs."""
        limit = RETENTION_LIMITS.get(policy, 7)
        policy_snaps = sorted(
            [s for s in self._snapshots.values() if s.retention_policy == policy],
            key=lambda s: s.created_at,
        )
        pruned: list[str] = []
        while len(policy_snaps) > limit:
            oldest = policy_snaps.pop(0)
            oldest.status = "ARCHIVED"
            del self._snapshots[oldest.snapshot_id]
            pruned.append(oldest.snapshot_id)
            LOGGER.info("backup_manager snapshot_id=%s pruned policy=%s", oldest.snapshot_id, policy)
        return pruned

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_snapshot(self, snapshot_id: str) -> BackupSnapshot | None:
        return self._snapshots.get(snapshot_id)

    def list_snapshots(self, backup_type: str | None = None) -> list[BackupSnapshot]:
        snaps = list(self._snapshots.values())
        if backup_type:
            snaps = [s for s in snaps if s.backup_type == backup_type]
        return sorted(snaps, key=lambda s: s.created_at)

    def _get_or_raise(self, snapshot_id: str) -> BackupSnapshot:
        snap = self._snapshots.get(snapshot_id)
        if not snap:
            raise KeyError(f"Snapshot '{snapshot_id}' not found.")
        return snap
