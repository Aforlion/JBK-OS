from __future__ import annotations

from typing import Any


class ExecutiveMeetingReport:
    """Summarizes minutes, decisions, and outcomes of an executive session (BR-040-012)."""

    def __init__(
        self,
        meeting_id: str,
        meeting_type: str,
        attendance: list[str],
        agenda: list[dict[str, Any]],
        discussions: dict[str, str],
        decisions: list[dict[str, Any]],
        action_items: list[dict[str, Any]],
        unresolved_items: list[dict[str, Any]],
        knowledge_candidates: list[str],
        consensus_achieved: bool = True,
    ) -> None:
        self.meeting_id = meeting_id
        self.meeting_type = meeting_type
        self.attendance = list(attendance or [])
        self.agenda = list(agenda or [])
        self.discussions = dict(discussions or {})
        self.decisions = list(decisions or [])
        self.action_items = list(action_items or [])
        self.unresolved_items = list(unresolved_items or [])
        self.knowledge_candidates = list(knowledge_candidates or [])
        self.consensus_achieved = consensus_achieved

    def summary(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "meeting_type": self.meeting_type,
            "attendance_count": len(self.attendance),
            "consensus_achieved": self.consensus_achieved,
            "decision_count": len(self.decisions),
            "action_item_count": len(self.action_items),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "meeting_type": self.meeting_type,
            "attendance": list(self.attendance),
            "agenda": list(self.agenda),
            "discussions": dict(self.discussions),
            "decisions": list(self.decisions),
            "action_items": list(self.action_items),
            "unresolved_items": list(self.unresolved_items),
            "knowledge_candidates": list(self.knowledge_candidates),
            "consensus_achieved": self.consensus_achieved,
        }
