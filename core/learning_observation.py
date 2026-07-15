from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

OBSERVATION_SOURCES = (
    "COMPLETED_PROJECT",
    "CLIENT_FEEDBACK",
    "ORGANIZATIONAL_MEMORY",
    "KNOWLEDGE_REGISTRY",
    "STRATEGIC_INTELLIGENCE",
    "MARKET_RESEARCH",
    "TECHNOLOGY_RESEARCH",
    "REGULATORY_CHANGE",
    "INTERNAL_EXPERIMENT",
    "EXTERNAL_PUBLICATION",
)


class LearningObservation:
    """Represents a piece of raw operational or research data ingested by JBK OS.

    BR-055-005: Confidence scores are mandatory.
    BR-055-010: Fully serializable.
    """

    def __init__(
        self,
        observation_id: str,
        title: str,
        source: str,
        description: str,
        confidence: float,       # value from 0.0 to 1.0
        domain: str = "AI",      # domain classification: AI, Healthcare, Retail etc.
        evidence: list[str] | None = None,
        created_at: str | None = None,
    ) -> None:
        if source not in OBSERVATION_SOURCES:
            raise ValueError(f"Invalid observation source: '{source}'. Must be one of {OBSERVATION_SOURCES}")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence score must be between 0.0 and 1.0 (got {confidence})")

        self.observation_id = observation_id
        self.title = title
        self.source = source
        self.description = description
        self.confidence = confidence
        self.domain = domain
        self.evidence = evidence or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "title": self.title,
            "source": self.source,
            "description": self.description,
            "confidence": self.confidence,
            "domain": self.domain,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }
