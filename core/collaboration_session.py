from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.shared_workspace import SharedWorkspace


class CollaborationRole(str, Enum):
    LEAD = "LEAD"
    CONTRIBUTOR = "CONTRIBUTOR"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    OBSERVER = "OBSERVER"


class CollaborationParticipantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    COMPLETED = "COMPLETED"


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVIEW = "REVIEW"
    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    ESCALATED = "ESCALATED"


class CollaborationParticipant:
    """Tracks a single skill participant registration (BR-039-002)."""

    def __init__(
        self,
        skill_id: str,
        role: CollaborationRole,
        status: CollaborationParticipantStatus = CollaborationParticipantStatus.IDLE,
    ) -> None:
        self.skill_id = skill_id
        self.role = role
        self.status = status
        self.assigned_tasks: list[str] = []
        self.deliverables: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "role": self.role.value,
            "status": self.status.value,
            "assigned_tasks": list(self.assigned_tasks),
            "deliverables": list(self.deliverables),
        }


class CollaborationMessage:
    """A single record in the session's audit log trail (BR-039-010)."""

    def __init__(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        artifact_reference: str | None = None,
        content: str = "",
        timestamp: str | None = None,
    ) -> None:
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type  # e.g., TASK_ASSIGNMENT, ARTIFACT_SUBMISSION, REVIEW_FEEDBACK
        self.artifact_reference = artifact_reference
        self.content = content
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "artifact_reference": self.artifact_reference,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class CollaborationSession:
    """Orchestrates the active collaboration lifecycle (BR-039-001)."""

    def __init__(self, session_id: str, work_order_id: str) -> None:
        if not session_id:
            raise ValueError("Session ID is required.")
        if not work_order_id:
            raise ValueError("Work order ID is required.")

        self.session_id = session_id
        self.work_order_id = work_order_id
        self.participants: dict[str, CollaborationParticipant] = {}
        self.workspace = SharedWorkspace()
        self.status = SessionStatus.ACTIVE
        self.audit_trail: list[CollaborationMessage] = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def register_participant(self, participant: CollaborationParticipant) -> None:
        self.participants[participant.skill_id] = participant

    def log_message(self, message: CollaborationMessage) -> None:
        self.audit_trail.append(message)

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "work_order_id": self.work_order_id,
            "participant_count": len(self.participants),
            "status": self.status.value,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "work_order_id": self.work_order_id,
            "participants": {k: v.to_dict() for k, v in self.participants.items()},
            "workspace": self.workspace.to_dict(),
            "status": self.status.value,
            "audit_trail": [msg.to_dict() for msg in self.audit_trail],
            "created_at": self.created_at,
        }
