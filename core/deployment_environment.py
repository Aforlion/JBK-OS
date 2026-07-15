from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

ENVIRONMENT_TYPES = ("DEVELOPMENT", "TESTING", "STAGING", "PRODUCTION", "DEMO")
ENVIRONMENT_STATUSES = ("PENDING", "ACTIVE", "DEGRADED", "FAILED")


class DeploymentEnvironment:
    """Represents a JBK OS deployment target environment.

    BR-052-005: Configuration profiles remain isolated per environment.
    BR-052-008: Fully serializable.
    """

    def __init__(
        self,
        env_id: str,
        env_type: str,
        config_profile: dict[str, Any] | None = None,
        status: str = "PENDING",
        created_at: str | None = None,
    ) -> None:
        if env_type not in ENVIRONMENT_TYPES:
            raise ValueError(f"Invalid environment type: {env_type}. Must be one of {ENVIRONMENT_TYPES}")
        if status not in ENVIRONMENT_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {ENVIRONMENT_STATUSES}")

        self.env_id = env_id
        self.env_type = env_type
        self.status = status
        self.config_profile = config_profile or {}
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "env_id": self.env_id,
            "env_type": self.env_type,
            "status": self.status,
            "config_profile": self.config_profile,
            "created_at": self.created_at,
        }
