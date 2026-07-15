from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ExecutiveActionItem:
    """Follow-up action item generated from meeting decisions (BR-040-008)."""

    def __init__(
        self,
        owner: str,
        description: str,
        priority: str,
        due_date: str,
        originating_decision: str | None = None,
    ) -> None:
        self.owner = owner
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.originating_decision = originating_decision

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "originating_decision": self.originating_decision,
        }


class ExecutiveDecision:
    """Formal decision recorded during executive meetings (BR-040-007)."""

    def __init__(
        self,
        decision_id: str,
        proposal: str,
        outcome: str,
        rationale: str,
        confidence: float,
        proposer: str | None = None,
    ) -> None:
        self.decision_id = decision_id
        self.proposal = proposal
        self.outcome = outcome
        self.rationale = rationale
        self.confidence = max(0.0, min(1.0, confidence))
        self.proposer = proposer

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "proposal": self.proposal,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "proposer": self.proposer,
        }


class AgendaItem:
    """A single topic scheduled on the meeting agenda (BR-040-004)."""

    def __init__(
        self,
        title: str,
        owner: str,
        priority: str = "MEDIUM",
        discussion: str = "",
        decisions: list[ExecutiveDecision] | None = None,
    ) -> None:
        self.title = title
        self.owner = owner
        self.priority = priority
        self.discussion = discussion
        self.decisions = list(decisions or [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "owner": self.owner,
            "priority": self.priority,
            "discussion": self.discussion,
            "decisions": [d.to_dict() for d in self.decisions],
        }


class ExecutiveMeeting:
    """Tracks the active session and governance state of the meeting (BR-040-001)."""

    def __init__(
        self,
        meeting_id: str,
        meeting_type: str,
        participants: list[str] | None = None,
        agenda: list[AgendaItem] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        status: str = "DRAFT",
    ) -> None:
        if not meeting_id:
            raise ValueError("Meeting ID is required.")
        if not meeting_type:
            raise ValueError("Meeting Type is required.")

        self.meeting_id = meeting_id
        self.meeting_type = meeting_type
        self.participants = list(participants or [])
        self.agenda = list(agenda or [])
        self.start_time = start_time or datetime.now(timezone.utc).isoformat()
        self.end_time = end_time
        self.status = status

    def summary(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "meeting_type": self.meeting_type,
            "participant_count": len(self.participants),
            "agenda_count": len(self.agenda),
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "meeting_type": self.meeting_type,
            "participants": list(self.participants),
            "agenda": [item.to_dict() for item in self.agenda],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
        }
