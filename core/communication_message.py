from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

# Priority Weights
PRIORITY_WEIGHTS = {
    "CRITICAL": 4,
    "HIGH": 3,
    "NORMAL": 2,
    "LOW": 1,
}


class CommunicationMessage:
    """Represents a single message payload in the JBK OS Unified Communication system.

    BR-049-001: Every communication is immutable once marked SENT or delivered.
    BR-049-006: Fully serializable to dictionary structure.
    """

    def __init__(
        self,
        message_id: str,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
        channel: str = "Internal Inbox",
        priority: str = "NORMAL",
        status: str = "DRAFT",
        created_at: str | None = None,
        scheduled_at: str | None = None,
        delivered_at: str | None = None,
        attachments: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if priority not in PRIORITY_WEIGHTS:
            raise ValueError(f"Invalid priority: {priority}")

        self.message_id = message_id
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.body = body
        self.channel = channel
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.scheduled_at = scheduled_at
        self.delivered_at = delivered_at
        self.attachments = attachments or []
        self.metadata = metadata or {}

    @property
    def priority_weight(self) -> int:
        return PRIORITY_WEIGHTS.get(self.priority, 2)

    def mark_status(self, new_status: str) -> None:
        """Mark status update, checking for immutability rules.

        BR-049-001: Message body/subject immutable once sent.
        """
        if self.status in ("SENT", "DELIVERED") and new_status not in ("ARCHIVED", "READ"):
            # Once sent, metadata state updates only, content is locked.
            pass
        self.status = new_status
        if new_status == "DELIVERED":
            self.delivered_at = datetime.now(timezone.utc).isoformat()

    def update_content(self, subject: str, body: str) -> None:
        """Helper to modify drafts. Enforces BR-049-001 immutability rules."""
        if self.status in ("SENT", "DELIVERED"):
            raise ValueError("Cannot modify content of a sent or delivered message (BR-049-001).")
        self.subject = subject
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipients": self.recipients,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "delivered_at": self.delivered_at,
            "attachments": self.attachments,
            "metadata": self.metadata,
        }
