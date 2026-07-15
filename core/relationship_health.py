from __future__ import annotations

from typing import Any

class RelationshipHealth:
    """Calculates and holds relationship health metrics for a client."""

    STATUS_EXCELLENT = "Excellent"
    STATUS_HEALTHY = "Healthy"
    STATUS_WATCH = "Watch"
    STATUS_AT_RISK = "At Risk"
    STATUS_CRITICAL = "Critical"

    def __init__(
        self,
        health_status: str = STATUS_HEALTHY,
        trust_score: float = 70.0,
        satisfaction_score: float = 5.0,
        failed_projects_count: int = 0,
        open_complaints: int = 0,
    ) -> None:
        self.health_status = health_status
        self.trust_score = trust_score
        self.satisfaction_score = satisfaction_score
        self.failed_projects_count = failed_projects_count
        self.open_complaints = open_complaints

    @classmethod
    def calculate(
        cls,
        trust_score: float,
        satisfaction_score: float,
        failed_projects_count: int = 0,
        open_complaints: int = 0,
    ) -> RelationshipHealth:
        """Continuously recalculate relationship health based on scores, complaints, and delivery history."""
        # Critical conditions
        if trust_score < 35.0 or satisfaction_score < 1.5 or open_complaints >= 3 or failed_projects_count >= 3:
            status = cls.STATUS_CRITICAL
        # At Risk conditions
        elif trust_score < 50.0 or satisfaction_score < 2.5 or failed_projects_count >= 2:
            status = cls.STATUS_AT_RISK
        # Watch conditions
        elif trust_score < 70.0 or satisfaction_score < 3.5 or open_complaints > 0 or failed_projects_count > 0:
            status = cls.STATUS_WATCH
        # Excellent conditions
        elif trust_score >= 85.0 and satisfaction_score >= 4.5 and failed_projects_count == 0 and open_complaints == 0:
            status = cls.STATUS_EXCELLENT
        # Default Healthy
        else:
            status = cls.STATUS_HEALTHY

        return cls(
            health_status=status,
            trust_score=trust_score,
            satisfaction_score=satisfaction_score,
            failed_projects_count=failed_projects_count,
            open_complaints=open_complaints,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_status": self.health_status,
            "trust_score": self.trust_score,
            "satisfaction_score": self.satisfaction_score,
            "failed_projects_count": self.failed_projects_count,
            "open_complaints": self.open_complaints,
        }
