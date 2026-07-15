from __future__ import annotations

import unittest
from typing import Any
from core.integration_adapter import IntegrationAdapter
from core.integration_manifest import IntegrationManifest
from core.integration_auth import IntegrationAuth
from core.integration_framework import (
    IntegrationFramework,
    IntegrationRegistry,
    GoogleWorkspaceAdapter,
    GitHubAdapter,
    SlackAdapter,
)


class MockCustomAdapter(IntegrationAdapter):
    """Custom mocked integration connector."""

    def __init__(self, adapter_id: str) -> None:
        super().__init__(adapter_id, "MockProvider", "1.0.0", ["run"])
        self.manifest = IntegrationManifest(
            provider_name="MockProvider",
            version="1.0.0",
            auth_type="API Key",
            supported_operations=["run"],
            capabilities=["✓ Run Action"],
        )
        self.health_state = "HEALTHY"
        self.fail_execute = False

    def connect(self, auth_config: dict[str, Any]) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        self.is_connected = False
        return True

    def health_check(self) -> str:
        return self.health_state

    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.fail_execute:
            return {"success": False, "error": "Simulated Endpoint Failure"}
        if operation not in self.supported_operations:
            return {"success": False, "error": "Operation Unsupported"}
        return {"success": True, "result": "Done"}


class TestIntegrationFramework(unittest.TestCase):

    def setUp(self) -> None:
        self.auth = IntegrationAuth()
        self.framework = IntegrationFramework(self.auth)

        # Register standard connectors
        self.google = GoogleWorkspaceAdapter()
        self.github = GitHubAdapter()
        self.slack = SlackAdapter()

        self.framework.registry.register_adapter(self.google)
        self.framework.registry.register_adapter(self.github)
        self.framework.registry.register_adapter(self.slack)

        # Store mock auth references
        self.auth.store_auth_reference("google-workspace", "OAuth2", "REF-GWS-001")
        self.auth.store_auth_reference("github", "Bearer Token", "REF-GH-001")
        self.auth.store_auth_reference("slack", "API Key", "REF-SLACK-001")

    def test_registry_registration_and_activation(self) -> None:
        """Adapters can be registered and disabled."""
        self.assertTrue(self.framework.registry.is_enabled("google-workspace"))
        
        self.framework.registry.disable_adapter("google-workspace")
        self.assertFalse(self.framework.registry.is_enabled("google-workspace"))

        self.framework.registry.enable_adapter("google-workspace")
        self.assertTrue(self.framework.registry.is_enabled("google-workspace"))

    def test_capability_discovery(self) -> None:
        """BR-050-007: Connectors advertise capabilities."""
        caps = self.framework.list_capabilities("google-workspace")
        self.assertTrue(len(caps) > 0)
        self.assertIn("Upload File", caps)

    def test_auth_isolation_details(self) -> None:
        """BR-050-005: Authentication details are isolated."""
        auth_config = self.auth.get_auth_config("google-workspace")
        self.assertEqual(auth_config["auth_type"], "OAuth2")
        self.assertEqual(auth_config["credential_ref_id"], "REF-GWS-001")

    def test_execute_operation_success(self) -> None:
        res = self.framework.execute_operation(
            adapter_id="google-workspace",
            operation="upload_file",
            params={"file_name": "Requirements.docx"},
        )
        self.assertTrue(res["success"])
        self.assertIn("Executed Google Workspace", res["data"]["result"])

    def test_unsupported_operation_returns_structured_error(self) -> None:
        """BR-050-008: Unsupported operations return structured errors."""
        res = self.framework.execute_operation(
            adapter_id="google-workspace",
            operation="delete_database",  # Not in supported list
            params={},
        )
        self.assertFalse(res["success"])
        self.assertIn("not supported", res["error"])

    def test_graceful_failure_handling(self) -> None:
        """BR-050-004: Execution failure does not crash framework, returns structured error."""
        custom = MockCustomAdapter("mock-connector")
        custom.fail_execute = True
        self.framework.registry.register_adapter(custom)
        self.auth.store_auth_reference("mock-connector", "API Key", "REF-001")

        # Execute with low retry limits for fast test runs
        res = self.framework.execute_operation(
            adapter_id="mock-connector",
            operation="run",
            params={},
            retry_policy={"max_retries": 1, "backoff_factor": 0.01},
        )
        self.assertFalse(res["success"])
        self.assertIn("Execution failed", res["error"])

    def test_circuit_breaker_blocks_execution(self) -> None:
        """Circuit breaker opens and blocks calls after successive errors."""
        custom = MockCustomAdapter("mock-breaker")
        custom.fail_execute = True
        self.framework.registry.register_adapter(custom)
        self.auth.store_auth_reference("mock-breaker", "API Key", "REF-001")

        policy = {"max_retries": 0, "backoff_factor": 0.01}
        # Force 3 failures to trip circuit breaker
        self.framework.execute_operation("mock-breaker", "run", {}, policy)
        self.framework.execute_operation("mock-breaker", "run", {}, policy)
        self.framework.execute_operation("mock-breaker", "run", {}, policy)

        # 4th call should be blocked immediately by circuit breaker
        res = self.framework.execute_operation("mock-breaker", "run", {}, policy)
        self.assertFalse(res["success"])
        self.assertIn("Circuit breaker open", res["error"])

    def test_manifest_serialization(self) -> None:
        """BR-050-009: Integration configurations support serialization."""
        manifest = self.google.manifest
        d = manifest.to_dict()
        self.assertEqual(d["provider_name"], "Google Workspace")
        self.assertEqual(d["auth_type"], "OAuth2")

    def test_audit_trail_created_on_execution(self) -> None:
        """BR-050-010: Every action creates an audit record."""
        self.framework.execute_operation("google-workspace", "upload_file", {})
        trail = self.framework.get_audit_trail()
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0]["adapter_id"], "google-workspace")
        self.assertEqual(trail[0]["operation"], "upload_file")

    def test_health_check_reporting(self) -> None:
        """BR-050-006: Connectors expose health checks."""
        custom = MockCustomAdapter("health-connector")
        self.framework.registry.register_adapter(custom)
        
        # Verify offline state
        self.assertEqual(custom.health_check(), "HEALTHY")  # Default health check mocked
        self.assertEqual(self.google.health_check(), "UNHEALTHY")  # Not connected yet

        # Connect
        self.auth.store_auth_reference("google-workspace", "OAuth2", "REF-GWS-001")
        self.framework.execute_operation("google-workspace", "upload_file", {})
        self.assertEqual(self.google.health_check(), "HEALTHY")


if __name__ == "__main__":
    unittest.main()
