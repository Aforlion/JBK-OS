from __future__ import annotations

import hashlib
from typing import Any
from datetime import datetime, timezone


class SecretReference:
    """Stores references only to credentials and passwords.

    BR-051-005: Secrets are never exposed to business engines.
    """

    def __init__(self, secret_id: str, provider: str, reference_hash: str | None = None) -> None:
        self.secret_id = secret_id
        self.provider = provider
        self.created_at = datetime.now(timezone.utc).isoformat()
        # Enforce that no clear values are carried
        self.reference_hash = reference_hash or hashlib.sha256(secret_id.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_id": self.secret_id,
            "provider": self.provider,
            "created_at": self.created_at,
            "reference_hash": self.reference_hash,
        }
