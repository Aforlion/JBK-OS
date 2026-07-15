"""Specification 041 — Autonomous Company Mode: CompanyHealthSnapshot domain model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class HealthStatus(str):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class CompanyHealthSnapshot:
    """Holistic health measurement across all company dimensions.

    Scores are in the range [0.0, 1.0].  The overall health_score is a
    weighted average.  Status is derived from the overall score:

        >= 0.75  → HEALTHY
        >= 0.50  → DEGRADED
        <  0.50  → CRITICAL
    """

    # Dimension weights (must sum to 1.0)
    _WEIGHTS: dict[str, float] = {
        "portfolio_health": 0.25,
        "delivery_health": 0.25,
        "financial_health": 0.15,
        "strategic_health": 0.15,
        "workforce_health": 0.10,
        "customer_health": 0.10,
    }

    def __init__(
        self,
        portfolio_health: float = 1.0,
        delivery_health: float = 1.0,
        financial_health: float = 1.0,
        strategic_health: float = 1.0,
        workforce_health: float = 1.0,
        customer_health: float = 1.0,
        snapshot_id: str | None = None,
        notes: dict[str, str] | None = None,
    ) -> None:
        self.snapshot_id: str = snapshot_id or f"HSN-{uuid.uuid4().hex[:8].upper()}"
        self.timestamp: str = datetime.now(timezone.utc).isoformat()

        self.portfolio_health: float = self._clamp(portfolio_health)
        self.delivery_health: float = self._clamp(delivery_health)
        self.financial_health: float = self._clamp(financial_health)
        self.strategic_health: float = self._clamp(strategic_health)
        self.workforce_health: float = self._clamp(workforce_health)
        self.customer_health: float = self._clamp(customer_health)

        self.notes: dict[str, str] = notes or {}

        # Computed
        self.health_score: float = self._compute_overall()
        self.status: str = self._derive_status()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _compute_overall(self) -> float:
        dimensions = {
            "portfolio_health": self.portfolio_health,
            "delivery_health": self.delivery_health,
            "financial_health": self.financial_health,
            "strategic_health": self.strategic_health,
            "workforce_health": self.workforce_health,
            "customer_health": self.customer_health,
        }
        return round(
            sum(self._WEIGHTS[k] * v for k, v in dimensions.items()),
            4,
        )

    def _derive_status(self) -> str:
        if self.health_score >= 0.75:
            return "HEALTHY"
        if self.health_score >= 0.50:
            return "DEGRADED"
        return "CRITICAL"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def dimension_scores(self) -> dict[str, float]:
        return {
            "portfolio_health": self.portfolio_health,
            "delivery_health": self.delivery_health,
            "financial_health": self.financial_health,
            "strategic_health": self.strategic_health,
            "workforce_health": self.workforce_health,
            "customer_health": self.customer_health,
        }

    def weakest_dimension(self) -> tuple[str, float]:
        """Return the name and score of the lowest-scoring dimension."""
        scores = self.dimension_scores()
        key = min(scores, key=lambda k: scores[k])
        return key, scores[key]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "health_score": self.health_score,
            "status": self.status,
            "dimensions": self.dimension_scores(),
            "notes": self.notes,
        }

    def summary(self) -> dict[str, Any]:
        dim, score = self.weakest_dimension()
        return {
            "snapshot_id": self.snapshot_id,
            "health_score": self.health_score,
            "status": self.status,
            "weakest_dimension": dim,
            "weakest_score": score,
        }

    def __repr__(self) -> str:
        return (
            f"<CompanyHealthSnapshot id={self.snapshot_id!r} "
            f"score={self.health_score} status={self.status!r}>"
        )
