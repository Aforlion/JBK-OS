from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.learning_observation import LearningObservation
from core.learning_recommendation import LearningRecommendation


class ContinuousLearningReport:
    """Immutable final report outlining learnings and knowledge gaps.

    BR-055-008: Learning reports shall be immutable.
    BR-055-010: Fully serializable.
    """

    _FROZEN = False

    def __init__(
        self,
        report_id: str,
        observations: list[LearningObservation],
        recommendations: list[LearningRecommendation],
        duplicate_observations: list[str],
        learning_domains: list[str],
        confidence_scores: dict[str, float],
        recommended_research_topics: list[str],
        recommended_new_skills: list[str],
        recommended_new_plugins: list[str],
        executive_summary: str = "",
        generated_at: str | None = None,
    ) -> None:
        self.report_id = report_id
        self.observations = observations
        self.recommendations = recommendations
        self.duplicate_observations = duplicate_observations
        self.learning_domains = learning_domains
        self.confidence_scores = confidence_scores
        self.recommended_research_topics = recommended_research_topics
        self.recommended_new_skills = recommended_new_skills
        self.recommended_new_plugins = recommended_new_plugins
        self.executive_summary = executive_summary
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self._FROZEN = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_FROZEN", False):
            raise AttributeError(f"ContinuousLearningReport is immutable. Cannot set '{name}'.")
        super().__setattr__(name, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "observations": [o.to_dict() for o in self.observations],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "duplicate_observations": self.duplicate_observations,
            "learning_domains": self.learning_domains,
            "confidence_scores": self.confidence_scores,
            "recommended_research_topics": self.recommended_research_topics,
            "recommended_new_skills": self.recommended_new_skills,
            "recommended_new_plugins": self.recommended_new_plugins,
            "executive_summary": self.executive_summary,
            "generated_at": self.generated_at,
        }
