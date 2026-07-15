from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class Session:
    """Tracks session lifecycles and expirations.

    BR-051-008: Expired sessions are invalid.
    """

    def __init__(
        self,
        session_id: str,
        identity_id: str,
        expires_at: str,
        created_at: str | None = None,
        last_activity: str | None = None,
        status: str = "ACTIVE",
    ) -> None:
        self.session_id = session_id
        self.identity_id = identity_id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.expires_at = expires_at
        self.last_activity = last_activity or self.created_at
        self.status = status  # ACTIVE, EXPIRED, TERMINATED

    def is_valid(self) -> bool:
        """Verify if session has expired or been terminated."""
        if self.status != "ACTIVE":
            return False
        
        now = datetime.now(timezone.utc)
        try:
            exp = datetime.fromisoformat(self.expires_at)
            if hasattr(exp, "tzinfo") and exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now >= exp:
                self.status = "EXPIRED"
                return False
        except Exception:
            return False
        return True

    def touch(self, lifetime_minutes: int = 30) -> None:
        """Extend expiration on active session."""
        if not self.is_valid():
            return
        now = datetime.now(timezone.utc)
        self.last_activity = now.isoformat()
        self.expires_at = (now + timedelta(minutes=lifetime_minutes)).isoformat()

    def terminate(self) -> None:
        self.status = "TERMINATED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "identity_id": self.identity_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_activity": self.last_activity,
            "status": self.status,
        }
