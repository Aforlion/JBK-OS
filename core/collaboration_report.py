from __future__ import annotations

from typing import Any


class CollaborationReport:
    """Summarizes the final collaborative outcome and execution telemetry (BR-039-014)."""

    def __init__(
        self,
        session_id: str,
        participants: list[dict[str, Any]],
        timeline: list[dict[str, Any]],
        reviews: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
        consensus_reached: bool,
        recommendations: list[str],
        final_artifact_id: str | None = None,
        reasoning: str = "",
    ) -> None:
        self.session_id = session_id
        self.participants = list(participants or [])
        self.timeline = list(timeline or [])
        self.reviews = list(reviews or [])
        self.conflicts = list(conflicts or [])
        self.consensus_reached = consensus_reached
        self.recommendations = list(recommendations or [])
        self.final_artifact_id = final_artifact_id
        self.reasoning = reasoning

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "consensus_reached": self.consensus_reached,
            "participant_count": len(self.participants),
            "conflict_count": len(self.conflicts),
            "final_artifact_id": self.final_artifact_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "participants": list(self.participants),
            "timeline": list(self.timeline),
            "reviews": list(self.reviews),
            "conflicts": list(self.conflicts),
            "consensus_reached": self.consensus_reached,
            "recommendations": list(self.recommendations),
            "final_artifact_id": self.final_artifact_id,
            "reasoning": self.reasoning,
        }
