from __future__ import annotations

import hashlib
import json
from typing import Any
from datetime import datetime, timezone

BACKUP_TYPES = ("FULL", "INCREMENTAL", "CONFIGURATION", "REGISTRY", "PROJECT", "KNOWLEDGE")
BACKUP_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CORRUPTED", "ARCHIVED")


class BackupSnapshot:
    """Represents a point-in-time backup of JBK OS operational data.

    BR-054-007: Supports point-in-time restoration.
    BR-054-010: Serializable.
    """

    def __init__(
        self,
        snapshot_id: str,
        backup_type: str,
        kernel_version: str,
        assets: dict[str, Any] | None = None,
        status: str = "PENDING",
        created_at: str | None = None,
        retention_policy: str = "DAILY",   # DAILY, WEEKLY, MONTHLY, MANUAL
    ) -> None:
        if backup_type not in BACKUP_TYPES:
            raise ValueError(f"Invalid backup type: '{backup_type}'. Must be one of {BACKUP_TYPES}")
        if status not in BACKUP_STATUSES:
            raise ValueError(f"Invalid backup status: '{status}'. Must be one of {BACKUP_STATUSES}")

        self.snapshot_id = snapshot_id
        self.backup_type = backup_type
        self.kernel_version = kernel_version
        self.assets = assets or {}
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.retention_policy = retention_policy
        self.asset_count = len(self.assets)
        self.checksum: str = ""
        self.validation_status: str = "UNVERIFIED"

    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum over serialized asset payload."""
        payload = json.dumps(self.assets, sort_keys=True, default=str).encode()
        self.checksum = hashlib.sha256(payload).hexdigest()
        return self.checksum

    def verify_checksum(self) -> bool:
        """Verify stored checksum matches current payload (BR-054-002, BR-054-003)."""
        if not self.checksum:
            self.validation_status = "UNVERIFIED"
            return False
        payload = json.dumps(self.assets, sort_keys=True, default=str).encode()
        current = hashlib.sha256(payload).hexdigest()
        if current == self.checksum:
            self.validation_status = "VALID"
            return True
        self.validation_status = "CORRUPTED"
        self.status = "CORRUPTED"
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "backup_type": self.backup_type,
            "kernel_version": self.kernel_version,
            "asset_count": self.asset_count,
            "status": self.status,
            "created_at": self.created_at,
            "retention_policy": self.retention_policy,
            "checksum": self.checksum,
            "validation_status": self.validation_status,
        }
