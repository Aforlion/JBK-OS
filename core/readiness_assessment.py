from __future__ import annotations

from typing import Any


class ReadinessAssessment:
    """Aggregates subsystem readiness percentages to form a scorecard.

    BR-056-012: The scorecard aggregates subsystem readiness.
    BR-056-007: Serializable.
    """

    def __init__(
        self,
        kernel_score: float = 100.0,
        governance_score: float = 100.0,
        operations_score: float = 100.0,
        intelligence_score: float = 100.0,
        executive_score: float = 100.0,
        ai_score: float = 100.0,
        security_score: float = 100.0,
        deployment_score: float = 100.0,
        recovery_score: float = 100.0,
        documentation_score: float = 100.0,
        testing_score: float = 100.0,
    ) -> None:
        self.kernel = kernel_score
        self.governance = governance_score
        self.operations = operations_score
        self.intelligence = intelligence_score
        self.executive = executive_score
        self.ai = ai_score
        self.security = security_score
        self.deployment = deployment_score
        self.recovery = recovery_score
        self.documentation = documentation_score
        self.testing = testing_score

    @property
    def overall_score(self) -> float:
        """Calculate overall average score across all scorecard items."""
        scores = [
            self.kernel,
            self.governance,
            self.operations,
            self.intelligence,
            self.executive,
            self.ai,
            self.security,
            self.deployment,
            self.recovery,
            self.documentation,
            self.testing,
        ]
        return round(sum(scores) / len(scores), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_scores": {
                "Kernel": self.kernel,
                "Governance": self.governance,
                "Business Operations": self.operations,
                "Intelligence": self.intelligence,
                "Executive Systems": self.executive,
                "AI": self.ai,
                "Security": self.security,
                "Deployment": self.deployment,
                "Recovery": self.recovery,
                "Documentation": self.documentation,
                "Testing": self.testing,
            },
            "overall_score": self.overall_score,
        }
