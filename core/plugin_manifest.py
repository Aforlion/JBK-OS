from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class PluginAuthor:
    def __init__(self, name: str, email: str = "", organization: str = "") -> None:
        self.name = name
        self.email = email
        self.organization = organization

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "email": self.email, "organization": self.organization}


class PluginCapability:
    """Advertised operation a plugin exposes (BR-053-009)."""

    def __init__(self, capability_id: str, name: str, description: str = "") -> None:
        self.capability_id = capability_id
        self.name = name
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        return {"capability_id": self.capability_id, "name": self.name, "description": self.description}


class PluginDependency:
    """Declares a plugin's dependency on another plugin or kernel version."""

    def __init__(self, dependency_id: str, min_version: str = "0.0.0", max_version: str = "999.0.0") -> None:
        self.dependency_id = dependency_id
        self.min_version = min_version
        self.max_version = max_version

    def to_dict(self) -> dict[str, Any]:
        return {"dependency_id": self.dependency_id, "min_version": self.min_version, "max_version": self.max_version}


class PluginPermission:
    """A named access request a plugin must declare (BR-053-005)."""

    VALID_PERMISSIONS = {
        "read_knowledge_registry",
        "access_ai_gateway",
        "send_communications",
        "access_crm",
        "read_client_portal",
        "invoke_integration_framework",
        "write_audit_log",
        "read_projects",
    }

    def __init__(self, permission_id: str, reason: str = "") -> None:
        if permission_id not in self.VALID_PERMISSIONS:
            raise ValueError(f"Unknown plugin permission: '{permission_id}'. Must be one of {sorted(self.VALID_PERMISSIONS)}")
        self.permission_id = permission_id
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {"permission_id": self.permission_id, "reason": self.reason}


class PluginManifest:
    """Full plugin descriptor required before installation (BR-053-004).

    BR-053-008: Fully serializable.
    """

    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        author: PluginAuthor,
        description: str = "",
        category: str = "general",
        minimum_kernel_version: str = "1.0.0",
        maximum_kernel_version: str = "999.0.0",
        required_permissions: list[PluginPermission] | None = None,
        dependencies: list[PluginDependency] | None = None,
        capabilities: list[PluginCapability] | None = None,
    ) -> None:
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.category = category
        self.minimum_kernel_version = minimum_kernel_version
        self.maximum_kernel_version = maximum_kernel_version
        self.required_permissions = required_permissions or []
        self.dependencies = dependencies or []
        self.capabilities = capabilities or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "author": self.author.to_dict(),
            "description": self.description,
            "category": self.category,
            "minimum_kernel_version": self.minimum_kernel_version,
            "maximum_kernel_version": self.maximum_kernel_version,
            "required_permissions": [p.to_dict() for p in self.required_permissions],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "capabilities": [c.to_dict() for c in self.capabilities],
        }
