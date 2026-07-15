from __future__ import annotations

import time
import logging
from typing import Any

from core.integration_adapter import IntegrationAdapter
from core.integration_manifest import IntegrationManifest
from core.integration_auth import IntegrationAuth

LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------------
# V1 Mocked Connectors (Fully Functional Interfaces)
# ------------------------------------------------------------------

class GoogleWorkspaceAdapter(IntegrationAdapter):
    """Google Workspace Connector (Gmail, Calendar, Drive, Docs, Sheets)."""

    def __init__(self, adapter_id: str = "google-workspace") -> None:
        supported = ["upload_file", "download_file", "search_files", "send_email", "create_event"]
        super().__init__(adapter_id, "Google Workspace", "1.0.0", supported)
        self.manifest = IntegrationManifest(
            provider_name="Google Workspace",
            version="1.0.0",
            auth_type="OAuth2",
            supported_operations=supported,
            capabilities=["Upload File", "Download File", "Search Files", "Create Folder", "Share File"],
        )

    def connect(self, auth_config: dict[str, Any]) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        self.is_connected = False
        return True

    def health_check(self) -> str:
        return "HEALTHY" if self.is_connected else "UNHEALTHY"

    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation not in self.supported_operations:
            return {"success": False, "error": f"Operation {operation} not supported (BR-050-008)."}
        
        # Simulated responses
        return {
            "success": True,
            "operation": operation,
            "provider": self.provider_name,
            "data": {"result": f"Executed Google Workspace {operation} successfully."},
        }


class GitHubAdapter(IntegrationAdapter):
    """GitHub Repository and Actions Connector."""

    def __init__(self, adapter_id: str = "github") -> None:
        supported = ["create_issue", "create_pull_request", "trigger_workflow"]
        super().__init__(adapter_id, "GitHub", "1.0.0", supported)
        self.manifest = IntegrationManifest(
            provider_name="GitHub",
            version="1.0.0",
            auth_type="Bearer Token",
            supported_operations=supported,
            capabilities=["✓ Open Issue", "✓ Create PR", "✓ Read Repo", "✓ Run Action"],
        )

    def connect(self, auth_config: dict[str, Any]) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        self.is_connected = False
        return True

    def health_check(self) -> str:
        return "HEALTHY" if self.is_connected else "UNHEALTHY"

    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation not in self.supported_operations:
            return {"success": False, "error": f"Operation {operation} not supported (BR-050-008)."}
        
        return {
            "success": True,
            "operation": operation,
            "provider": self.provider_name,
            "data": {"result": f"Executed GitHub {operation} successfully."},
        }


class SlackAdapter(IntegrationAdapter):
    """Slack Messaging and Notifications Connector."""

    def __init__(self, adapter_id: str = "slack") -> None:
        supported = ["send_message", "read_messages"]
        super().__init__(adapter_id, "Slack", "1.0.0", supported)
        self.manifest = IntegrationManifest(
            provider_name="Slack",
            version="1.0.0",
            auth_type="API Key",
            supported_operations=supported,
            capabilities=["✓ Send Notification", "✓ Read Thread"],
        )

    def connect(self, auth_config: dict[str, Any]) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        self.is_connected = False
        return True

    def health_check(self) -> str:
        return "HEALTHY" if self.is_connected else "UNHEALTHY"

    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation not in self.supported_operations:
            return {"success": False, "error": f"Operation {operation} not supported (BR-050-008)."}
        
        return {
            "success": True,
            "operation": operation,
            "provider": self.provider_name,
            "data": {"result": f"Executed Slack {operation} successfully."},
        }


# ------------------------------------------------------------------
# Registry and Framework Orchestrator
# ------------------------------------------------------------------

class IntegrationRegistry:
    """Tracks installed, enabled, and health statuses of active connectors."""

    def __init__(self) -> None:
        self._adapters: dict[str, IntegrationAdapter] = {}
        self._statuses: dict[str, bool] = {}  # enabled/disabled

    def register_adapter(self, adapter: IntegrationAdapter) -> None:
        self._adapters[adapter.adapter_id] = adapter
        self._statuses[adapter.adapter_id] = True

    def enable_adapter(self, adapter_id: str) -> None:
        if adapter_id in self._statuses:
            self._statuses[adapter_id] = True

    def disable_adapter(self, adapter_id: str) -> None:
        if adapter_id in self._statuses:
            self._statuses[adapter_id] = False

    def is_enabled(self, adapter_id: str) -> bool:
        return self._statuses.get(adapter_id, False)

    def get_adapter(self, adapter_id: str) -> IntegrationAdapter | None:
        return self._adapters.get(adapter_id)

    def list_adapters(self) -> list[IntegrationAdapter]:
        return list(self._adapters.values())


class IntegrationFramework:
    """Standardized Observability routing manager for all third-party integrations.

    BR-050-001: Business engines must never call third-party APIs directly.
    BR-050-004: Gracefully handles failures without crashing JBK OS.
    BR-050-010: Every integration action creates an audit record.
    """

    def __init__(self, auth_manager: IntegrationAuth | None = None) -> None:
        self.registry = IntegrationRegistry()
        self.auth = auth_manager or IntegrationAuth()
        self._audit_trail: list[dict[str, Any]] = []

        # Circuit Breaker states: maps adapter_id -> error_count
        self._circuit_breakers: dict[str, int] = {}
        self._circuit_threshold = 3

    def execute_operation(
        self,
        adapter_id: str,
        operation: str,
        params: dict[str, Any],
        retry_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Routes operation call to the appropriate adapter with retry policies and circuit breakers.

        BR-050-002: Enforces all external communications pass through framework.
        """
        # Audit Log Start (BR-050-010)
        audit_record = {
            "timestamp": time.time(),
            "adapter_id": adapter_id,
            "operation": operation,
            "status": "INITIATED",
        }
        self._audit_trail.append(audit_record)

        if not self.registry.is_enabled(adapter_id):
            audit_record["status"] = "FAILED"
            audit_record["error"] = "Integration is disabled."
            return {"success": False, "error": f"Integration {adapter_id} is disabled."}

        adapter = self.registry.get_adapter(adapter_id)
        if not adapter:
            audit_record["status"] = "FAILED"
            audit_record["error"] = "Integration not found."
            return {"success": False, "error": f"Integration {adapter_id} not found."}

        # Circuit Breaker Check
        if self._circuit_breakers.get(adapter_id, 0) >= self._circuit_threshold:
            audit_record["status"] = "BLOCKED"
            audit_record["error"] = "Circuit Breaker open due to consecutive failures."
            return {"success": False, "error": f"Circuit breaker open for integration: {adapter_id}"}

        # Retries & Rate Limit handling (Exponential backoff)
        retries = 3
        backoff = 0.1
        if retry_policy:
            retries = retry_policy.get("max_retries", retries)
            backoff = retry_policy.get("backoff_factor", backoff)

        last_error = ""
        for attempt in range(retries + 1):
            try:
                # Ensure connected
                if not adapter.is_connected:
                    auth_config = self.auth.get_auth_config(adapter_id)
                    adapter.connect(auth_config)

                result = adapter.execute(operation, params)
                
                # Verify result structure
                if result.get("success", False):
                    # Reset failure history on success
                    self._circuit_breakers[adapter_id] = 0
                    audit_record["status"] = "SUCCESS"
                    return result
                else:
                    last_error = result.get("error", "Unknown execute failure")

            except Exception as e:
                last_error = str(e)
                # Exponential backoff delay
                time.sleep(backoff * (2 ** attempt))

        # Record failure to Circuit Breaker
        self._circuit_breakers[adapter_id] = self._circuit_breakers.get(adapter_id, 0) + 1
        audit_record["status"] = "FAILED"
        audit_record["error"] = last_error

        # BR-050-004: Graceful failure return instead of crashing
        return {
            "success": False,
            "error": f"Execution failed on {adapter_id}: {last_error}",
            "failed": True,
        }

    def list_capabilities(self, adapter_id: str) -> list[str]:
        """Discovery method for AI Assistant to scan integration capability lists (BR-050-007)."""
        adapter = self.registry.get_adapter(adapter_id)
        if adapter and hasattr(adapter, "manifest"):
            return adapter.manifest.capabilities
        return []

    def get_audit_trail(self) -> list[dict[str, Any]]:
        return list(self._audit_trail)
