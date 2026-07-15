from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.certification_requirement import CertificationRequirement
from core.readiness_assessment import ReadinessAssessment

CERTIFICATION_STATUSES = ("CERTIFIED", "CONDITIONALLY_CERTIFIED", "NOT_CERTIFIED")
VERDICTS = ("APPROVED FOR PRODUCTION", "CONDITIONALLY APPROVED", "NOT APPROVED")


class CertificationReport:
    """Immutable audit certification summary outlining the final operational status.

    BR-056-005: Certification reports are immutable.
    BR-056-007: Serializable.
    """

    _FROZEN = False

    def __init__(
        self,
        certification_id: str,
        version: str,
        build_number: str,
        readiness_score: float,
        scorecard: ReadinessAssessment,
        passed_requirements: list[CertificationRequirement],
        failed_requirements: list[CertificationRequirement],
        warnings: list[str],
        blockers: list[str],
        recommendations: list[str],
        executive_summary: str,
        certification_status: str,
        verdict: str,
        generated_at: str | None = None,
    ) -> None:
        if certification_status not in CERTIFICATION_STATUSES:
            raise ValueError(f"Invalid status: '{certification_status}'. Must be one of {CERTIFICATION_STATUSES}")
        if verdict not in VERDICTS:
            raise ValueError(f"Invalid verdict: '{verdict}'. Must be one of {VERDICTS}")

        self.certification_id = certification_id
        self.version = version
        self.build_number = build_number
        self.readiness_score = readiness_score
        self.scorecard = scorecard
        self.passed_requirements = passed_requirements
        self.failed_requirements = failed_requirements
        self.warnings = warnings
        self.blockers = blockers
        self.recommendations = recommendations
        self.executive_summary = executive_summary
        self.certification_status = certification_status
        self.verdict = verdict
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self._FROZEN = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_FROZEN", False):
            raise AttributeError(f"CertificationReport is immutable. Cannot set '{name}'.")
        super().__setattr__(name, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "certification_id": self.certification_id,
            "version": self.version,
            "build_number": self.build_number,
            "certification_date": self.generated_at,
            "readiness_score": self.readiness_score,
            "subsystem_scores": self.scorecard.to_dict()["subsystem_scores"],
            "passed_requirements": [r.to_dict() for r in self.passed_requirements],
            "failed_requirements": [r.to_dict() for r in self.failed_requirements],
            "warnings": self.warnings,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "executive_summary": self.executive_summary,
            "certification_status": self.certification_status,
            "verdict": self.verdict,
        }
class MockVersionRegistry:
    """Mock version registry matching update signature."""
    def __init__(self):
        self.installed_version = None
        self.certification_details = {}
    def record(self, event_type, version, environment, success, extra=None):
        self.installed_version = version
        self.certification_details = extra or {}
