from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

class ClientInteraction:
    """Represents a single recorded interaction with a client."""

    def __init__(
        self,
        interaction_id: str,
        client_id: str,
        interaction_type: str,
        description: str,
        created_by: str = "system",
        outcome: str = "",
        timestamp: str | None = None,
    ) -> None:
        self.interaction_id = interaction_id
        self.client_id = client_id
        self.interaction_type = interaction_type.strip().lower()
        self.description = description.strip()
        self.created_by = created_by
        self.outcome = outcome.strip()
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize interaction to dictionary."""
        return {
            "interaction_id": self.interaction_id,
            "client_id": self.client_id,
            "interaction_type": self.interaction_type,
            "description": self.description,
            "created_by": self.created_by,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }
