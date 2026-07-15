from __future__ import annotations

from typing import Any


class IntegrationManifest:
    """Defines capabilities, limits, and configuration details for an integration.

    BR-050-007: Connectors advertise supported capabilities.
    BR-050-009: Fully serializable.
    """

    def __init__(
        self,
        provider_name: str,
        version: str,
        auth_type: str,  # OAuth2, API Key, Token, Basic, Service Account
        required_scopes: list[str] | None = None,
        supported_operations: list[str] | None = None,
        rate_limit_per_minute: int = 60,
        capabilities: list[str] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.version = version
        self.auth_type = auth_type
        self.required_scopes = required_scopes or []
        self.supported_operations = supported_operations or []
        self.rate_limit_per_minute = rate_limit_per_minute
        self.capabilities = capabilities or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "version": self.version,
            "auth_type": self.auth_type,
            "required_scopes": self.required_scopes,
            "supported_operations": self.supported_operations,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "capabilities": self.capabilities,
        }
