from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.plugin_manifest import PluginManifest

PLUGIN_STATUSES = ("DISCOVERED", "INSTALLED", "ENABLED", "DISABLED", "FAILED", "REMOVED")


class Plugin:
    """Represents an installed plugin with full lifecycle state (BR-053-008).

    Lifecycle: DISCOVERED → INSTALLED → ENABLED ⇄ DISABLED → REMOVED
               Any state → FAILED on error.
    """

    def __init__(
        self,
        manifest: PluginManifest,
        status: str = "DISCOVERED",
        approved_permissions: list[str] | None = None,
        installed_at: str | None = None,
    ) -> None:
        if status not in PLUGIN_STATUSES:
            raise ValueError(f"Invalid plugin status: '{status}'")
        self.manifest = manifest
        self.status = status
        self.approved_permissions: list[str] = approved_permissions or []
        self.installed_at = installed_at or datetime.now(timezone.utc).isoformat()
        self.last_error: str | None = None

    @property
    def plugin_id(self) -> str:
        return self.manifest.plugin_id

    @property
    def version(self) -> str:
        return self.manifest.version

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.manifest.name,
            "version": self.version,
            "status": self.status,
            "approved_permissions": self.approved_permissions,
            "installed_at": self.installed_at,
            "last_error": self.last_error,
            "capabilities": [c.to_dict() for c in self.manifest.capabilities],
        }
