from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


# Valid channels
COMMUNICATION_CHANNELS = ("Email", "Slack", "Teams", "SMS", "WhatsApp", "Internal")

# Valid directions
COMMUNICATION_DIRECTIONS = ("OUTBOUND", "INBOUND")

# Valid statuses
COMMUNICATION_STATUSES = ("DRAFT", "QUEUED", "SENT", "DELIVERED", "FAILED", "READ", "ARCHIVED")

# Statuses after which content is immutable (BR-045-004)
IMMUTABLE_STATUSES = ("SENT", "DELIVERED", "READ")

# Valid priority levels
COMMUNICATION_PRIORITIES = ("HIGH", "MEDIUM", "LOW")


class Communication:
    """Represents a single outbound or inbound communication.

    BR-045-004: Content fields are immutable once status is SENT/DELIVERED/READ.
    BR-045-009: Every communication includes explainability metadata.
    BR-045-010: Must be serializable via to_dict().
    """

    def __init__(
        self,
        communication_id: str,
        channel: str,
        direction: str = "OUTBOUND",
        sender: str = "",
        recipient: str = "",
        subject: str = "",
        message: str = "",
        attachments: list[str] | None = None,
        priority: str = "MEDIUM",
        status: str = "DRAFT",
        created_at: str | None = None,
        sent_at: str | None = None,
        # Explainability metadata (BR-045-009)
        source_engine: str = "",
        triggering_event: str = "",
        reasoning: str = "",
    ) -> None:
        if channel not in COMMUNICATION_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}. Supported: {COMMUNICATION_CHANNELS}")
        if direction not in COMMUNICATION_DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction}. Must be OUTBOUND or INBOUND.")
        if status not in COMMUNICATION_STATUSES:
            raise ValueError(f"Invalid status: {status}.")
        if priority not in COMMUNICATION_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}.")

        self.communication_id = communication_id
        self.channel = channel
        self.direction = direction
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.message = message
        self.attachments = attachments or []
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.sent_at = sent_at

        # Explainability (BR-045-009)
        self.source_engine = source_engine
        self.triggering_event = triggering_event
        self.reasoning = reasoning

    def mark_sent(self) -> None:
        """Transition to SENT status and record timestamp."""
        self.status = "SENT"
        self.sent_at = datetime.now(timezone.utc).isoformat()

    def update_content(self, subject: str | None = None, message: str | None = None) -> None:
        """Update content fields. Raises if communication is immutable (BR-045-004)."""
        if self.status in IMMUTABLE_STATUSES:
            raise ValueError(
                f"Cannot modify communication {self.communication_id}: "
                f"content is immutable after status {self.status} (BR-045-004)."
            )
        if subject is not None:
            self.subject = subject
        if message is not None:
            self.message = message

    def to_dict(self) -> dict[str, Any]:
        """BR-045-010: Serializable."""
        return {
            "communication_id": self.communication_id,
            "channel": self.channel,
            "direction": self.direction,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "message": self.message,
            "attachments": self.attachments,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "source_engine": self.source_engine,
            "triggering_event": self.triggering_event,
            "reasoning": self.reasoning,
        }
