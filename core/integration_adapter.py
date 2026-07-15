from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IntegrationAdapter(ABC):
    """Abstract base class for all third-party system adapters.

    Every connector must inherit this class.
    """

    def __init__(self, adapter_id: str, provider_name: str, version: str, supported_operations: list[str]) -> None:
        self.adapter_id = adapter_id
        self.provider_name = provider_name
        self.version = version
        self.supported_operations = supported_operations
        self.is_connected = False

    @abstractmethod
    def connect(self, auth_config: dict[str, Any]) -> bool:
        """Initialize connection with credentials details."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection cleanly."""
        pass

    @abstractmethod
    def health_check(self) -> str:
        """Verify external endpoint availability. Returns HEALTHY or UNHEALTHY."""
        pass

    @abstractmethod
    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a target capability action. Returns operation results."""
        pass
