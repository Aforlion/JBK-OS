from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

# Valid identity types
IDENTITY_TYPES = ("EXECUTIVE", "CLIENT", "AI", "SERVICE_ACCOUNT")

# Valid identity statuses
IDENTITY_STATUSES = ("ACTIVE", "LOCKED", "INACTIVE")


class Identity:
    """Represents a human or non-human actor identity in JBK OS.

    BR-051-009: Permissions are fully serializable.
    """

    def __init__(
        self,
        identity_id: str,
        display_name: str,
        identity_type: str,
        status: str = "ACTIVE",
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        created_at: str | None = None,
        last_login: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if identity_type not in IDENTITY_TYPES:
            raise ValueError(f"Invalid identity type: {identity_type}. Must be one of {IDENTITY_TYPES}")
        if status not in IDENTITY_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {IDENTITY_STATUSES}")

        self.identity_id = identity_id
        self.display_name = display_name
        self.identity_type = identity_type
        self.status = status
        self.roles = roles or []
        self.permissions = permissions or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.last_login = last_login
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "display_name": self.display_name,
            "identity_type": self.identity_type,
            "status": self.status,
            "roles": self.roles,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "metadata": self.metadata,
        }
