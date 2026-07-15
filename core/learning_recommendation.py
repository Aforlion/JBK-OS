from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

RECOMMENDATION_CATEGORIES = (
    "KNOWLEDGE",
    "SKILL",
    "PROCESS",
    "STANDARD",
    "SPECIFICATION",
    "PLUGIN",
    "AI_EXECUTIVE",
    "INTEGRATION",
    "TRAINING",
    "RESEARCH",
)

RECOMMENDATION_PRIORITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


class LearningRecommendation:
    """An advisory strategic action identified to expand organizational intelligence.

    BR-055-004: Every recommendation requires explainability.
    BR-055-006: Prioritized.
    BR-055-010: Fully serializable.
    """

    def __init__(
        self,
        recommendation_id: str,
        title: str,
        category: str,
        priority: str,
        reasoning: str,
        confidence: float,
        evidence: list[str],
        affected_systems: list[str] | None = None,
        expected_value: str = "",
        implementation_difficulty: str = "MEDIUM",  # LOW, MEDIUM, HIGH
        created_at: str | None = None,
    ) -> None:
        if category not in RECOMMENDATION_CATEGORIES:
            raise ValueError(f"Invalid recommendation category: '{category}'. Must be one of {RECOMMENDATION_CATEGORIES}")
        if priority not in RECOMMENDATION_PRIORITIES:
            raise ValueError(f"Invalid priority: '{priority}'. Must be one of {RECOMMENDATION_PRIORITIES}")
        if not reasoning:
            raise ValueError("Explainability reasoning is mandatory (BR-055-004).")

        self.recommendation_id = recommendation_id
        self.title = title
        self.category = category
        self.priority = priority
        self.reasoning = reasoning
        self.confidence = confidence
        self.evidence = evidence
        self.affected_systems = affected_systems or []
        self.expected_value = expected_value
        self.implementation_difficulty = implementation_difficulty
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "affected_systems": self.affected_systems,
            "expected_value": self.expected_value,
            "implementation_difficulty": self.implementation_difficulty,
            "created_at": self.created_at,
        }
