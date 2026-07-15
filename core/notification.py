from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

# Valid severity levels (expanded for Spec 049)
NOTIFICATION_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


class Notification:
    """Represents an internal organizational notification.

    BR-049-005: Every automated notification includes originating engine.
    BR-049-006: Fully serializable to dict structure.
    """

    def __init__(
        self,
        notification_id: str,
        title: str,
        message: str,
        recipient_role: str,
        severity: str,
        source_engine: str,
        action_required: str,
        category: str = "General",
        created_at: str | None = None,
        read: bool = False,
    ) -> None:
        if not title or not title.strip():
            raise ValueError("Notification title is required.")
        if not message or not message.strip():
            raise ValueError("Notification message is required.")
        if not recipient_role or not recipient_role.strip():
            raise ValueError("Recipient role is required.")
        if severity not in NOTIFICATION_SEVERITIES:
            # Maintain backward compatibility with older "HIGH", "MEDIUM", "LOW" cases
            # If severity is not in the expanded tuple, raise unless it matches case insensitively
            if severity.upper() in NOTIFICATION_SEVERITIES:
                severity = severity.upper()
            else:
                raise ValueError(f"Invalid severity: {severity}. Must be one of {NOTIFICATION_SEVERITIES}")
        if not source_engine or not source_engine.strip():
            raise ValueError("Source engine is required.")
        if not action_required or not action_required.strip():
            raise ValueError("Action required is required.")

        self.notification_id = notification_id
        self.title = title.strip()
        self.message = message.strip()
        self.recipient_role = recipient_role.strip()
        self.severity = severity
        self.source_engine = source_engine.strip()
        self.action_required = action_required.strip()
        self.category = category
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.read = read

    @property
    def is_ceo_briefing(self) -> bool:
        """Flag notifications to show in CEO Briefing."""
        return self.severity in ("CRITICAL", "HIGH")

    def mark_read(self) -> None:
        self.read = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "recipient_role": self.recipient_role,
            "severity": self.severity,
            "source_engine": self.source_engine,
            "action_required": self.action_required,
            "category": self.category,
            "created_at": self.created_at,
            "read": self.read,
            "is_ceo_briefing": self.is_ceo_briefing,
        }
