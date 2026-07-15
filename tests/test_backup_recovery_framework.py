from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta
from typing import Any

from core.backup_snapshot import BackupSnapshot, BACKUP_TYPES
from core.recovery_plan import RecoveryPlan
from core.disaster_recovery_report import DisasterRecoveryReport
from core.backup_manager import BackupManager
from core.recovery_manager import RecoveryManager


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _test_assets() -> dict[str, Any]:
    return {
        "REGISTRY": {
            "workers": ["EXEC-001", "EXEC-002"],
            "projects": ["PROJ-001"],
        },
        "CONFIGURATION": {
            "ai_provider": "mock",
            "security": "strict",
        },
    }


def _make_snapshot(snap_id: str = "SNAP-001", btype: str = "FULL", ver: str = "1.0.0") -> BackupSnapshot:
    return BackupSnapshot(
        snapshot_id=snap_id,
        backup_type=btype,
        kernel_version=ver,
        assets=_test_assets(),
    )


# ---------------------------------------------------------------------------
# BackupSnapshot Model Tests
# ---------------------------------------------------------------------------

class TestBackupSnapshot(unittest.TestCase):

    def test_valid_snapshot_creation(self) -> None:
        snap = _make_snapshot()
        self.assertEqual(snap.snapshot_id, "SNAP-001")
        self.assertEqual(snap.status, "PENDING")
        self.assertEqual(snap.asset_count, 2)

    def test_invalid_type_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BackupSnapshot("S1", "DATABASE", "1.0.0")

    def test_checksum_computation(self) -> None:
        snap = _make_snapshot()
        checksum = snap.compute_checksum()
        self.assertEqual(len(checksum), 64)
        self.assertTrue(snap.verify_checksum())

    def test_checksum_verification_fails_on_mutation(self) -> None:
        """BR-054-002 + BR-054-003: Mutated assets must fail checksum validation."""
        snap = _make_snapshot()
        snap.compute_checksum()
        snap.assets["REGISTRY"]["workers"].append("HACKER")
        self.assertFalse(snap.verify_checksum())
        self.assertEqual(snap.validation_status, "CORRUPTED")

    def test_serialization(self) -> None:
        """BR-054-010: Snapshot is serializable."""
        snap = _make_snapshot()
        snap.compute_checksum()
        d = snap.to_dict()
        self.assertEqual(d["snapshot_id"], "SNAP-001")
        self.assertEqual(d["checksum"], snap.checksum)


# ---------------------------------------------------------------------------
# RecoveryPlan & DisasterRecoveryReport Model Tests
# ---------------------------------------------------------------------------

class TestRecoveryPlanAndReport(unittest.TestCase):

    def test_recovery_plan(self) -> None:
        plan = RecoveryPlan(
            recovery_id="REC-001",
            target_snapshot_id="SNAP-001",
            recovery_scope=["REGISTRY"],
        )
        self.assertEqual(plan.recovery_scope, ["REGISTRY"])
        self.assertIn("recovery_scope", plan.to_dict())

    def test_report_immutability(self) -> None:
        """BR-054-010: Reports are immutable."""
        report = DisasterRecoveryReport(
            recovery_id="REC-001",
            snapshot_id="SNAP-001",
            restored_assets=["REGISTRY"],
            failed_assets=[],
            integrity_results={"checksum_match": True},
            warnings=[],
            recovery_time_seconds=0.05,
        )
        self.assertTrue(report.success)
        with self.assertRaises(AttributeError):
            report.snapshot_id = "SNAP-TAMPERED"


# ---------------------------------------------------------------------------
# BackupManager Tests
# ---------------------------------------------------------------------------

class TestBackupManager(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = BackupManager(kernel_version="1.0.0")

    def test_create_snapshot_computes_checksum(self) -> None:
        snap = self.mgr.create_snapshot("FULL", _test_assets())
        self.assertEqual(snap.status, "COMPLETED")
        self.assertEqual(snap.validation_status, "UNVERIFIED")
        self.assertTrue(self.mgr.verify_snapshot(snap.snapshot_id))
        self.assertEqual(snap.validation_status, "VALID")

    def test_create_incremental_snapshot(self) -> None:
        base = self.mgr.create_snapshot("FULL", _test_assets())
        inc = self.mgr.create_incremental_snapshot(base.snapshot_id, {"PROJECT": {"id": "P2"}})
        self.assertEqual(inc.backup_type, "INCREMENTAL")
        self.assertIn("PROJECT", inc.assets)
        self.assertIn("REGISTRY", inc.assets)

    def test_corruption_detection(self) -> None:
        """BR-054-003: Corrupted snapshots are identified."""
        snap = self.mgr.create_snapshot("FULL", _test_assets())
        self.mgr.corrupt_snapshot(snap.snapshot_id)
        self.assertFalse(self.mgr.verify_snapshot(snap.snapshot_id))

    def test_retention_policy_pruning(self) -> None:
        """BR-054-006: Configurable retention policies prune old backups."""
        # Create 8 DAILY snapshots (Limit is 7)
        for i in range(8):
            self.mgr.create_snapshot("FULL", _test_assets(), retention_policy="DAILY")
            # Force older timestamp
            snap_id = f"SNAP-{i+1:04d}"
            snap = self.mgr.get_snapshot(snap_id)
            if snap:
                snap.created_at = (datetime.now(timezone.utc) - timedelta(days=8-i)).isoformat()

        pruned = self.mgr.apply_retention_policy("DAILY")
        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0], "SNAP-0001")
        self.assertIsNone(self.mgr.get_snapshot("SNAP-0001"))


# ---------------------------------------------------------------------------
# RecoveryManager Tests
# ---------------------------------------------------------------------------

class TestRecoveryManager(unittest.TestCase):

    def setUp(self) -> None:
        self.backup_mgr = BackupManager(kernel_version="1.0.0")
        self.recovery_mgr = RecoveryManager(kernel_version="1.0.0")
        self.snapshot = self.backup_mgr.create_snapshot("FULL", _test_assets())
        self.plan = RecoveryPlan("REC-001", self.snapshot.snapshot_id, ["REGISTRY", "CONFIGURATION"])

    def test_successful_recovery(self) -> None:
        report = self.recovery_mgr.execute_recovery(self.plan, self.snapshot)
        self.assertTrue(report.success)
        self.assertEqual(report.restored_assets, ["REGISTRY", "CONFIGURATION"])
        self.assertEqual(len(self.recovery_mgr.get_history()), 1)

    def test_corrupted_backup_rejected(self) -> None:
        """BR-054-003: Corrupted backup triggers rejection report."""
        self.backup_mgr.corrupt_snapshot(self.snapshot.snapshot_id)
        report = self.recovery_mgr.execute_recovery(self.plan, self.snapshot)
        self.assertFalse(report.success)
        self.assertEqual(report.restored_assets, [])
        self.assertIn("checksum mismatch", report.warnings[0])

    def test_version_incompatibility_rejected(self) -> None:
        """Recovery halts on version mismatch."""
        incompat_snap = BackupSnapshot("SNAP-INC", "FULL", "2.0.0", _test_assets())
        incompat_snap.compute_checksum()
        
        report = self.recovery_mgr.execute_recovery(self.plan, incompat_snap)
        self.assertFalse(report.success)
        self.assertEqual(report.restored_assets, [])
        self.assertIn("Version mismatch", report.warnings[0])

    def test_failed_asset_causes_consistency_rollback(self) -> None:
        """BR-054-004: Failure of one registry rolls back to keep state consistent."""
        report = self.recovery_mgr.execute_recovery(self.plan, self.snapshot, fail_on_asset="CONFIGURATION")
        self.assertFalse(report.success)
        self.assertEqual(report.restored_assets, [])
        self.assertIn("CONFIGURATION", report.failed_assets)


if __name__ == "__main__":
    unittest.main()
