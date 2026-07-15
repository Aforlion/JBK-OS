from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone


class OpportunityStatus(str, Enum):
    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class OpportunityBrief:
    def __init__(
        self,
        opportunity_id: str,
        client_request_text: str,
        business_domain: str,
        business_problems: list[str],
        desired_outcomes: list[str],
        known_constraints: list[str],
        missing_information: list[str],
        recommended_next_questions: list[str],
        complexity_rating: str,
        confidence_score: float,
        recommended_next_step: str,
        status: OpportunityStatus | str = OpportunityStatus.DRAFT,
        created_at: str | None = None,
    ) -> None:
        self.opportunity_id = opportunity_id
        self.client_request_text = client_request_text or ""
        self.business_domain = business_domain or "Unknown"
        self.business_problems = business_problems or []
        self.desired_outcomes = desired_outcomes or []
        self.known_constraints = known_constraints or []
        self.missing_information = missing_information or []
        self.recommended_next_questions = recommended_next_questions or []
        self.complexity_rating = complexity_rating or "Low"
        self.confidence_score = float(confidence_score)
        self.recommended_next_step = recommended_next_step or "Clarification"
        self.status = (
            status if isinstance(status, OpportunityStatus) else OpportunityStatus(status)
        )
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "business_domain": self.business_domain,
            "complexity_rating": self.complexity_rating,
            "confidence_score": self.confidence_score,
            "status": self.status.value,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "client_request_text": self.client_request_text,
            "business_domain": self.business_domain,
            "business_problems": list(self.business_problems),
            "desired_outcomes": list(self.desired_outcomes),
            "known_constraints": list(self.known_constraints),
            "missing_information": list(self.missing_information),
            "recommended_next_questions": list(self.recommended_next_questions),
            "complexity_rating": self.complexity_rating,
            "confidence_score": self.confidence_score,
            "recommended_next_step": self.recommended_next_step,
            "status": self.status.value,
            "created_at": self.created_at,
        }
