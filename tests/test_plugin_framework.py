from __future__ import annotations

import unittest
from typing import Any

from core.plugin_manifest import (
    PluginManifest,
    PluginAuthor,
    PluginCapability,
    PluginDependency,
    PluginPermission,
)
from core.plugin import Plugin, PLUGIN_STATUSES
from core.plugin_execution_report import PluginExecutionReport
from core.plugin_manager import PluginManager, PluginRegistry


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _author(name: str = "JBK Technologies") -> PluginAuthor:
    return PluginAuthor(name=name, email="dev@jbk.tech", organization="JBK")


def _manifest(
    plugin_id: str = "salesforce-connector",
    name: str = "Salesforce Connector",
    version: str = "1.0.0",
    permissions: list[PluginPermission] | None = None,
    dependencies: list[PluginDependency] | None = None,
    capabilities: list[PluginCapability] | None = None,
    min_kernel: str = "1.0.0",
    max_kernel: str = "999.0.0",
) -> PluginManifest:
    caps = capabilities or [
        PluginCapability("cap-crm-sync", "CRM Synchronization"),
        PluginCapability("cap-lead-export", "Lead Export"),
    ]
    return PluginManifest(
        plugin_id=plugin_id,
        name=name,
        version=version,
        author=_author(),
        description="Salesforce CRM integration plugin.",
        category="crm",
        minimum_kernel_version=min_kernel,
        maximum_kernel_version=max_kernel,
        required_permissions=permissions or [],
        dependencies=dependencies or [],
        capabilities=caps,
    )


def _manager() -> PluginManager:
    return PluginManager(kernel_version="1.0.0")


# ---------------------------------------------------------------------------
# PluginManifest Tests
# ---------------------------------------------------------------------------

class TestPluginManifest(unittest.TestCase):

    def test_manifest_creation(self) -> None:
        m = _manifest()
        self.assertEqual(m.plugin_id, "salesforce-connector")
        self.assertEqual(len(m.capabilities), 2)

    def test_manifest_serialization(self) -> None:
        """BR-053-008: Manifest serializes fully."""
        d = _manifest().to_dict()
        self.assertIn("plugin_id", d)
        self.assertIn("capabilities", d)
        self.assertIn("author", d)
        self.assertEqual(len(d["capabilities"]), 2)

    def test_invalid_permission_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PluginPermission("delete_everything")

    def test_valid_permissions_accepted(self) -> None:
        p = PluginPermission("access_ai_gateway", reason="Needs AI for analysis")
        self.assertEqual(p.permission_id, "access_ai_gateway")


# ---------------------------------------------------------------------------
# Plugin Model Tests
# ---------------------------------------------------------------------------

class TestPluginModel(unittest.TestCase):

    def test_plugin_defaults_to_discovered(self) -> None:
        p = Plugin(_manifest())
        self.assertEqual(p.status, "DISCOVERED")

    def test_all_statuses_valid(self) -> None:
        for status in PLUGIN_STATUSES:
            p = Plugin(_manifest(), status=status)
            self.assertEqual(p.status, status)

    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Plugin(_manifest(), status="RUNNING")

    def test_plugin_serialization(self) -> None:
        d = Plugin(_manifest(), status="INSTALLED").to_dict()
        self.assertEqual(d["plugin_id"], "salesforce-connector")
        self.assertEqual(d["status"], "INSTALLED")
        self.assertIn("capabilities", d)


# ---------------------------------------------------------------------------
# PluginExecutionReport Tests
# ---------------------------------------------------------------------------

class TestPluginExecutionReport(unittest.TestCase):

    def _report(self, status: str = "SUCCESS") -> PluginExecutionReport:
        return PluginExecutionReport(
            execution_id="EXEC-0001",
            plugin_id="salesforce-connector",
            capability_id="cap-crm-sync",
            execution_time_ms=42.5,
            status=status,
            outputs={"synced": 5},
        )

    def test_report_immutability(self) -> None:
        """BR-053-007: Execution reports are immutable."""
        report = self._report()
        with self.assertRaises(AttributeError):
            report.status = "HACKED"

    def test_report_serialization(self) -> None:
        d = self._report().to_dict()
        self.assertEqual(d["execution_id"], "EXEC-0001")
        self.assertEqual(d["status"], "SUCCESS")
        self.assertEqual(d["outputs"]["synced"], 5)


# ---------------------------------------------------------------------------
# PluginManager — Manifest Validation
# ---------------------------------------------------------------------------

class TestPluginManagerValidation(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = _manager()

    def test_valid_manifest_passes(self) -> None:
        valid, errors = self.mgr.validate_manifest(_manifest())
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_plugin_id_fails(self) -> None:
        m = _manifest(plugin_id="")
        valid, errors = self.mgr.validate_manifest(m)
        self.assertFalse(valid)
        self.assertTrue(any("plugin_id" in e for e in errors))

    def test_kernel_below_minimum_fails(self) -> None:
        m = _manifest(min_kernel="2.0.0")
        valid, errors = self.mgr.validate_manifest(m)
        self.assertFalse(valid)
        self.assertTrue(any("below minimum" in e for e in errors))

    def test_kernel_above_maximum_fails(self) -> None:
        m = _manifest(max_kernel="0.5.0")
        valid, errors = self.mgr.validate_manifest(m)
        self.assertFalse(valid)
        self.assertTrue(any("exceeds maximum" in e for e in errors))


# ---------------------------------------------------------------------------
# PluginManager — Lifecycle
# ---------------------------------------------------------------------------

class TestPluginManagerLifecycle(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = _manager()

    def test_install_sets_installed_status(self) -> None:
        plugin = self.mgr.install(_manifest())
        self.assertEqual(plugin.status, "INSTALLED")
        self.assertIsNotNone(self.mgr.registry.get("salesforce-connector"))

    def test_install_invalid_manifest_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.mgr.install(_manifest(plugin_id=""))

    def test_enable_requires_approved_permissions(self) -> None:
        """BR-053-005: Permissions require explicit approval."""
        m = _manifest(permissions=[PluginPermission("access_crm")])
        self.mgr.install(m)
        with self.assertRaises(PermissionError):
            self.mgr.enable("salesforce-connector", approved_permissions=[])

    def test_enable_with_correct_permissions_succeeds(self) -> None:
        m = _manifest(permissions=[PluginPermission("access_crm")])
        self.mgr.install(m)
        self.mgr.enable("salesforce-connector", approved_permissions=["access_crm"])
        plugin = self.mgr.registry.get("salesforce-connector")
        self.assertEqual(plugin.status, "ENABLED")

    def test_enable_no_permissions_needed(self) -> None:
        self.mgr.install(_manifest())
        self.mgr.enable("salesforce-connector")
        self.assertEqual(self.mgr.registry.get("salesforce-connector").status, "ENABLED")

    def test_disable_sets_disabled_status(self) -> None:
        self.mgr.install(_manifest())
        self.mgr.enable("salesforce-connector")
        self.mgr.disable("salesforce-connector")
        self.assertEqual(self.mgr.registry.get("salesforce-connector").status, "DISABLED")

    def test_remove_deletes_from_registry(self) -> None:
        self.mgr.install(_manifest())
        self.mgr.remove("salesforce-connector")
        self.assertIsNone(self.mgr.registry.get("salesforce-connector"))

    def test_remove_unknown_plugin_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.mgr.remove("ghost-plugin")


# ---------------------------------------------------------------------------
# PluginManager — Dependency Resolution
# ---------------------------------------------------------------------------

class TestDependencyResolution(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = _manager()

    def test_missing_dependency_blocks_enable(self) -> None:
        """BR-053-006: Dependencies must be installed before activation."""
        dep = PluginDependency("base-crm-plugin")
        m = _manifest(dependencies=[dep])
        self.mgr.install(m)
        with self.assertRaises(RuntimeError) as ctx:
            self.mgr.enable("salesforce-connector")
        self.assertIn("base-crm-plugin", str(ctx.exception))

    def test_installed_dependency_allows_enable(self) -> None:
        # Install dependency first
        base_manifest = _manifest(plugin_id="base-crm-plugin", name="Base CRM", dependencies=[])
        self.mgr.install(base_manifest)

        dep = PluginDependency("base-crm-plugin")
        child = _manifest(dependencies=[dep])
        self.mgr.install(child)
        self.mgr.enable("salesforce-connector")   # Should succeed
        self.assertEqual(self.mgr.registry.get("salesforce-connector").status, "ENABLED")

    def test_out_of_range_dep_version_blocks_enable(self) -> None:
        base = _manifest(plugin_id="base-crm-plugin", name="Base CRM", version="0.5.0")
        self.mgr.install(base)
        dep = PluginDependency("base-crm-plugin", min_version="1.0.0")
        child = _manifest(dependencies=[dep])
        self.mgr.install(child)
        with self.assertRaises(RuntimeError) as ctx:
            self.mgr.enable("salesforce-connector")
        self.assertIn("out of range", str(ctx.exception))


# ---------------------------------------------------------------------------
# PluginManager — Execution & Isolation
# ---------------------------------------------------------------------------

class TestPluginExecution(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = _manager()
        self.mgr.install(_manifest())
        self.mgr.enable("salesforce-connector")

    def test_successful_execution(self) -> None:
        report = self.mgr.execute("salesforce-connector", "cap-crm-sync")
        self.assertEqual(report.status, "SUCCESS")
        self.assertGreater(report.execution_time_ms, 0)

    def test_execution_creates_audit_trail(self) -> None:
        """BR-053-007: Execution is auditable."""
        self.mgr.execute("salesforce-connector", "cap-lead-export")
        history = self.mgr.get_execution_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].capability_id, "cap-lead-export")

    def test_undeclared_capability_returns_failure(self) -> None:
        report = self.mgr.execute("salesforce-connector", "cap-delete-db")
        self.assertEqual(report.status, "FAILED")
        self.assertTrue(any("not declared" in e for e in report.errors))

    def test_disabled_plugin_execution_fails_gracefully(self) -> None:
        """BR-053-003: Plugin failures isolated from kernel."""
        self.mgr.disable("salesforce-connector")
        report = self.mgr.execute("salesforce-connector", "cap-crm-sync")
        self.assertEqual(report.status, "FAILED")
        self.assertTrue(any("not enabled" in e for e in report.errors))

    def test_executor_exception_isolates_to_plugin(self) -> None:
        """BR-053-003: Runtime exception in plugin sets FAILED status, kernel unaffected."""
        def bad_executor(params: dict) -> None:
            raise RuntimeError("Database connection lost!")

        self.mgr.register_executor("salesforce-connector", "cap-crm-sync", bad_executor)
        report = self.mgr.execute("salesforce-connector", "cap-crm-sync")
        self.assertEqual(report.status, "FAILED")
        self.assertEqual(self.mgr.registry.get("salesforce-connector").status, "FAILED")
        # Verify manager itself is still operational
        self.assertIsNotNone(self.mgr.registry)

    def test_custom_executor_used(self) -> None:
        self.mgr.register_executor("salesforce-connector", "cap-crm-sync",
                                   lambda p: {"synced": 99})
        report = self.mgr.execute("salesforce-connector", "cap-crm-sync")
        self.assertEqual(report.outputs["synced"], 99)


# ---------------------------------------------------------------------------
# PluginManager — Capability Discovery
# ---------------------------------------------------------------------------

class TestCapabilityDiscovery(unittest.TestCase):

    def test_list_capabilities_for_enabled_plugin(self) -> None:
        """BR-053-009: Capabilities are discoverable."""
        mgr = _manager()
        mgr.install(_manifest())
        mgr.enable("salesforce-connector")
        caps = mgr.list_capabilities("salesforce-connector")
        self.assertEqual(len(caps), 2)
        names = [c["name"] for c in caps]
        self.assertIn("CRM Synchronization", names)

    def test_list_all_enabled_capabilities(self) -> None:
        mgr = _manager()
        mgr.install(_manifest("p1", "Plugin One", capabilities=[PluginCapability("c1", "Cap One")]))
        mgr.install(_manifest("p2", "Plugin Two", capabilities=[PluginCapability("c2", "Cap Two")]))
        mgr.enable("p1")
        mgr.enable("p2")
        caps = mgr.list_capabilities()
        self.assertEqual(len(caps), 2)

    def test_disabled_plugin_not_in_global_discovery(self) -> None:
        mgr = _manager()
        mgr.install(_manifest())
        # NOT enabled
        caps = mgr.list_capabilities()
        self.assertEqual(len(caps), 0)


# ---------------------------------------------------------------------------
# PluginManager — Update
# ---------------------------------------------------------------------------

class TestPluginUpdate(unittest.TestCase):

    def test_update_replaces_version(self) -> None:
        """BR-053-010: Update preserves config and installs new version."""
        mgr = _manager()
        mgr.install(_manifest(version="1.0.0"))
        mgr.enable("salesforce-connector")

        updated = mgr.update(_manifest(version="1.1.0"))
        self.assertEqual(updated.version, "1.1.0")
        self.assertEqual(updated.status, "INSTALLED")

    def test_update_preserves_permissions(self) -> None:
        mgr = _manager()
        m = _manifest(permissions=[PluginPermission("access_crm")])
        mgr.install(m)
        mgr.enable("salesforce-connector", approved_permissions=["access_crm"])

        mgr.update(_manifest(version="1.1.0"))
        updated = mgr.registry.get("salesforce-connector")
        self.assertIn("access_crm", updated.approved_permissions)


# ---------------------------------------------------------------------------
# Registry Serialization
# ---------------------------------------------------------------------------

class TestRegistrySerialization(unittest.TestCase):

    def test_registry_serializes(self) -> None:
        """BR-053-008: Registry is serializable."""
        mgr = _manager()
        mgr.install(_manifest())
        d = mgr.registry.to_dict()
        self.assertIn("plugins", d)
        self.assertEqual(len(d["plugins"]), 1)
        self.assertEqual(d["plugins"][0]["plugin_id"], "salesforce-connector")


if __name__ == "__main__":
    unittest.main()
