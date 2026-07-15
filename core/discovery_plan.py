from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class DiscoveryPlan:
    def __init__(
        self,
        discovery_id: str,
        opportunity_id: str | None,
        conversation_objective: str,
        information_already_known: list[str],
        information_still_required: list[str],
        recommended_question_sequence: list[dict[str, Any]],
        conversation_categories: list[str],
        discovery_completeness: float,
        confidence_score: float,
        recommended_next_step: str,
        created_at: str | None = None,
    ) -> None:
        self.discovery_id = discovery_id
        self.opportunity_id = opportunity_id
        self.conversation_objective = conversation_objective or "Understand business goals"
        self.information_already_known = information_already_known or []
        self.information_still_required = information_still_required or []
        self.recommended_question_sequence = recommended_question_sequence or []
        self.conversation_categories = conversation_categories or []
        self.discovery_completeness = float(discovery_completeness)
        self.confidence_score = float(confidence_score)
        self.recommended_next_step = recommended_next_step or "Discovery Call"
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "discovery_id": self.discovery_id,
            "opportunity_id": self.opportunity_id,
            "discovery_completeness": self.discovery_completeness,
            "confidence_score": self.confidence_score,
            "recommended_next_step": self.recommended_next_step,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "discovery_id": self.discovery_id,
            "opportunity_id": self.opportunity_id,
            "conversation_objective": self.conversation_objective,
            "information_already_known": list(self.information_already_known),
            "information_still_required": list(self.information_still_required),
            "recommended_question_sequence": [dict(q) for q in self.recommended_question_sequence],
            "conversation_categories": list(self.conversation_categories),
            "discovery_completeness": self.discovery_completeness,
            "confidence_score": self.confidence_score,
            "recommended_next_step": self.recommended_next_step,
            "created_at": self.created_at,
        }
