from __future__ import annotations

import time
import logging
from typing import Any, Callable
from datetime import datetime, timezone

from core.plugin_manifest import PluginManifest
from core.plugin import Plugin
from core.plugin_execution_report import PluginExecutionReport

LOGGER = logging.getLogger(__name__)

# Current kernel version — used for compatibility checks
KERNEL_VERSION = "1.0.0"


def _parse_version(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0, 0, 0)


class PluginRegistry:
    """Tracks all plugins by ID across their lifecycle.

    BR-053-008: Registry is serializable.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def add(self, plugin: Plugin) -> None:
        self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> Plugin | None:
        return self._plugins.get(plugin_id)

    def remove(self, plugin_id: str) -> None:
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]

    def list_all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def list_enabled(self) -> list[Plugin]:
        return [p for p in self._plugins.values() if p.status == "ENABLED"]

    def to_dict(self) -> dict[str, Any]:
        return {"plugins": [p.to_dict() for p in self._plugins.values()]}


class PluginManager:
    """Manages the full plugin lifecycle: discover → validate → install → enable → execute → disable → update → remove.

    BR-053-001: Kernel closed for modification.
    BR-053-002: Plugins extend through public interfaces only.
    BR-053-003: Plugin failures never affect kernel.
    BR-053-004: Manifest validation is mandatory.
    BR-053-005: Permissions require explicit approval.
    BR-053-006: Dependencies resolved before activation.
    BR-053-007: Execution is auditable.
    BR-053-009: Capability discovery supported.
    BR-053-010: Updates preserve existing configuration.
    """

    def __init__(self, kernel_version: str = KERNEL_VERSION) -> None:
        self.kernel_version = kernel_version
        self.registry = PluginRegistry()
        self._exec_counter = 1
        self._execution_history: list[PluginExecutionReport] = []
        # Maps plugin_id -> callable executor (injected by tests or real implementations)
        self._executors: dict[str, dict[str, Callable[..., Any]]] = {}

    # ------------------------------------------------------------------
    # Validation (BR-053-004)
    # ------------------------------------------------------------------

    def validate_manifest(self, manifest: PluginManifest) -> tuple[bool, list[str]]:
        """Returns (is_valid, list_of_errors). Validates structure and version compatibility."""
        errors: list[str] = []

        if not manifest.plugin_id:
            errors.append("plugin_id is required.")
        if not manifest.name:
            errors.append("name is required.")
        if not manifest.version:
            errors.append("version is required.")
        if not manifest.author or not manifest.author.name:
            errors.append("author.name is required.")

        # Version compatibility check
        kernel = _parse_version(self.kernel_version)
        min_v = _parse_version(manifest.minimum_kernel_version)
        max_v = _parse_version(manifest.maximum_kernel_version)
        if kernel < min_v:
            errors.append(f"Kernel {self.kernel_version} is below minimum required {manifest.minimum_kernel_version}.")
        if kernel > max_v:
            errors.append(f"Kernel {self.kernel_version} exceeds maximum supported {manifest.maximum_kernel_version}.")

        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------

    def install(self, manifest: PluginManifest) -> Plugin:
        """Validate and install a plugin. Does NOT enable it (BR-053-004)."""
        valid, errors = self.validate_manifest(manifest)
        if not valid:
            raise ValueError(f"Manifest validation failed: {errors}")

        plugin = Plugin(manifest, status="INSTALLED")
        self.registry.add(plugin)
        LOGGER.info("plugin_manager plugin_id=%s version=%s action=INSTALLED", manifest.plugin_id, manifest.version)
        return plugin

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------

    def enable(self, plugin_id: str, approved_permissions: list[str] | None = None) -> None:
        """Enable a plugin after permission approval and dependency resolution (BR-053-005, BR-053-006)."""
        plugin = self._get_or_raise(plugin_id)

        # Permission enforcement (BR-053-005)
        required = {p.permission_id for p in plugin.manifest.required_permissions}
        approved = set(approved_permissions or [])
        missing_perms = required - approved
        if missing_perms:
            raise PermissionError(f"Missing approved permissions for '{plugin_id}': {missing_perms}")

        # Dependency resolution (BR-053-006)
        dep_errors = self._resolve_dependencies(plugin)
        if dep_errors:
            raise RuntimeError(f"Dependency resolution failed for '{plugin_id}': {dep_errors}")

        plugin.approved_permissions = list(approved)
        plugin.status = "ENABLED"
        LOGGER.info("plugin_manager plugin_id=%s action=ENABLED", plugin_id)

    def disable(self, plugin_id: str) -> None:
        plugin = self._get_or_raise(plugin_id)
        plugin.status = "DISABLED"
        LOGGER.info("plugin_manager plugin_id=%s action=DISABLED", plugin_id)

    # ------------------------------------------------------------------
    # Execution (BR-053-003, BR-053-007)
    # ------------------------------------------------------------------

    def execute(
        self,
        plugin_id: str,
        capability_id: str,
        params: dict[str, Any] | None = None,
    ) -> PluginExecutionReport:
        """Execute a plugin capability. Failures are isolated from the kernel (BR-053-003)."""
        exec_id = f"EXEC-{self._exec_counter:04d}"
        self._exec_counter += 1
        start = time.monotonic()
        params = params or {}

        plugin = self.registry.get(plugin_id)
        if not plugin or plugin.status != "ENABLED":
            report = PluginExecutionReport(
                execution_id=exec_id,
                plugin_id=plugin_id,
                capability_id=capability_id,
                execution_time_ms=0.0,
                status="FAILED",
                errors=[f"Plugin '{plugin_id}' is not enabled or not found."],
            )
            self._execution_history.append(report)
            return report

        # Verify capability is declared (BR-053-009)
        cap_ids = {c.capability_id for c in plugin.manifest.capabilities}
        if capability_id not in cap_ids:
            report = PluginExecutionReport(
                execution_id=exec_id,
                plugin_id=plugin_id,
                capability_id=capability_id,
                execution_time_ms=0.0,
                status="FAILED",
                errors=[f"Capability '{capability_id}' not declared by plugin '{plugin_id}'."],
            )
            self._execution_history.append(report)
            return report

        # Execute through registered callable, isolating any exception (BR-053-003)
        executor = self._executors.get(plugin_id, {}).get(capability_id)
        outputs: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []
        status = "SUCCESS"

        try:
            if executor:
                outputs = executor(params) or {}
            else:
                outputs = {"result": f"Plugin '{plugin_id}' capability '{capability_id}' executed (mock)."}
        except Exception as exc:
            # BR-053-003: Failure isolated — plugin goes to FAILED, kernel unaffected
            errors.append(str(exc))
            status = "FAILED"
            plugin.status = "FAILED"
            plugin.last_error = str(exc)
            LOGGER.warning("plugin_manager plugin_id=%s capability=%s ERROR=%s", plugin_id, capability_id, exc)

        elapsed_ms = (time.monotonic() - start) * 1000

        report = PluginExecutionReport(
            execution_id=exec_id,
            plugin_id=plugin_id,
            capability_id=capability_id,
            execution_time_ms=round(elapsed_ms, 3),
            status=status,
            outputs=outputs,
            warnings=warnings,
            errors=errors,
        )
        self._execution_history.append(report)
        return report

    def register_executor(self, plugin_id: str, capability_id: str, fn: Callable[..., Any]) -> None:
        """Inject a callable executor for a capability (used in tests and real connectors)."""
        self._executors.setdefault(plugin_id, {})[capability_id] = fn

    # ------------------------------------------------------------------
    # Update (BR-053-010)
    # ------------------------------------------------------------------

    def update(self, new_manifest: PluginManifest) -> Plugin:
        """Install a new version, preserving approved permissions where possible."""
        plugin_id = new_manifest.plugin_id
        existing = self.registry.get(plugin_id)
        preserved_permissions = existing.approved_permissions if existing else []

        # Disable existing first
        if existing and existing.status == "ENABLED":
            self.disable(plugin_id)

        valid, errors = self.validate_manifest(new_manifest)
        if not valid:
            raise ValueError(f"Update manifest validation failed: {errors}")

        updated_plugin = Plugin(new_manifest, status="INSTALLED", approved_permissions=preserved_permissions)
        self.registry.add(updated_plugin)
        LOGGER.info("plugin_manager plugin_id=%s version=%s action=UPDATED", plugin_id, new_manifest.version)
        return updated_plugin

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    def remove(self, plugin_id: str) -> None:
        plugin = self._get_or_raise(plugin_id)
        plugin.status = "REMOVED"
        self.registry.remove(plugin_id)
        LOGGER.info("plugin_manager plugin_id=%s action=REMOVED", plugin_id)

    # ------------------------------------------------------------------
    # Capability Discovery (BR-053-009)
    # ------------------------------------------------------------------

    def list_capabilities(self, plugin_id: str | None = None) -> list[dict[str, Any]]:
        """Return capability catalogue for one or all enabled plugins."""
        result: list[dict[str, Any]] = []
        plugins = [self.registry.get(plugin_id)] if plugin_id else self.registry.list_enabled()
        for p in plugins:
            if p:
                for cap in p.manifest.capabilities:
                    result.append({"plugin_id": p.plugin_id, "plugin_name": p.manifest.name, **cap.to_dict()})
        return result

    def get_execution_history(self) -> list[PluginExecutionReport]:
        return list(self._execution_history)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_raise(self, plugin_id: str) -> Plugin:
        plugin = self.registry.get(plugin_id)
        if not plugin:
            raise KeyError(f"Plugin '{plugin_id}' not found in registry.")
        return plugin

    def _resolve_dependencies(self, plugin: Plugin) -> list[str]:
        errors: list[str] = []
        for dep in plugin.manifest.dependencies:
            installed = self.registry.get(dep.dependency_id)
            if not installed or installed.status not in ("INSTALLED", "ENABLED"):
                errors.append(f"Dependency '{dep.dependency_id}' is not installed.")
            elif installed:
                dep_ver = _parse_version(installed.version)
                min_v = _parse_version(dep.min_version)
                max_v = _parse_version(dep.max_version)
                if not (min_v <= dep_ver <= max_v):
                    errors.append(f"Dependency '{dep.dependency_id}' version {installed.version} out of range [{dep.min_version}, {dep.max_version}].")
        return errors
