from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.communication_message import CommunicationMessage


class MessageThread:
    """A logical conversation thread grouping messages and participants.

    BR-049-008: Client conversations remain isolated.
    BR-049-009: Executive conversations are internal only.
    BR-049-006: Fully serializable to dict.
    """

    def __init__(
        self,
        thread_id: str,
        subject: str,
        participants: list[str],
        messages: list[CommunicationMessage] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.thread_id = thread_id
        self.subject = subject
        self.participants = participants
        self.messages: list[CommunicationMessage] = messages or []
        self.metadata = metadata or {}

    def add_message(self, message: CommunicationMessage) -> None:
        """Add a message to this thread, enforcing participant boundaries."""
        # Enforce that the sender must be in participants list
        if message.sender not in self.participants:
            self.participants.append(message.sender)
        
        # Enforce that all recipients are in the participants list
        for r in message.recipients:
            if r not in self.participants:
                self.participants.append(r)
                
        self.messages.append(message)

    def is_client_isolated(self) -> bool:
        """BR-049-008: Determines if this is a client isolated thread."""
        return self.metadata.get("client_isolated", False)

    def is_executive_internal(self) -> bool:
        """BR-049-009: Determines if this is an executive-only thread."""
        return self.metadata.get("executive_internal", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "subject": self.subject,
            "participants": self.participants,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
            "is_client_isolated": self.is_client_isolated(),
            "is_executive_internal": self.is_executive_internal(),
        }
