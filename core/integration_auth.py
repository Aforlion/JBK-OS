from __future__ import annotations

from typing import Any


class IntegrationAuth:
    """Manages credentials scopes and isolates credential configurations.

    BR-050-005: Authentication details are isolated from business logic.
    Stores references/identifiers to credentials rather than raw plain text secrets.
    """

    def __init__(self) -> None:
        # Maps adapter_id -> credential metadata details (references)
        self._auth_records: dict[str, dict[str, Any]] = {}

    def store_auth_reference(self, adapter_id: str, auth_type: str, credential_ref_id: str, extra_metadata: dict[str, Any] | None = None) -> None:
        """Stores reference pointer to credentials vault."""
        self._auth_records[adapter_id] = {
            "auth_type": auth_type,
            "credential_ref_id": credential_ref_id,
            "metadata": extra_metadata or {},
        }

    def get_auth_config(self, adapter_id: str) -> dict[str, Any]:
        """Return auth parameters (resolved mock config) for the connector."""
        record = self._auth_records.get(adapter_id)
        if not record:
            raise ValueError(f"No auth reference stored for integration: {adapter_id}")
        return {
            "auth_type": record["auth_type"],
            "credential_ref_id": record["credential_ref_id"],
            "resolved": True,
        }

    def delete_auth_reference(self, adapter_id: str) -> None:
        if adapter_id in self._auth_records:
            del self._auth_records[adapter_id]
