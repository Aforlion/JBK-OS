from __future__ import annotations

from typing import Any


class ValidationResult:
    """Captures the outcome of output validation (BR-038-007)."""

    def __init__(
        self,
        passed: bool,
        score: float,
        issues: list[str] | None = None,
        recommendations: list[str] | None = None,
    ) -> None:
        self.passed = passed
        self.score = max(0.0, min(1.0, score))
        self.issues = list(issues or [])
        self.recommendations = list(recommendations or [])

    def summary(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "issue_count": len(self.issues),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": list(self.issues),
            "recommendations": list(self.recommendations),
        }


class OutputValidator:
    """Default output validator checking completeness and required sections (BR-038-007)."""

    def validate(
        self,
        content: str,
        required_sections: list[str] | None = None,
        min_length: int = 10,
    ) -> ValidationResult:
        issues: list[str] = []
        recommendations: list[str] = []

        if not content or not content.strip():
            return ValidationResult(
                passed=False,
                score=0.0,
                issues=["Output is empty."],
                recommendations=["Ensure the AI provider returned content."],
            )

        # Check minimum length
        if len(content.strip()) < min_length:
            issues.append(f"Output is too short ({len(content.strip())} chars, minimum {min_length}).")
            recommendations.append("Consider increasing prompt specificity.")

        # Check required sections
        if required_sections:
            content_lower = content.lower()
            for section in required_sections:
                if section.lower() not in content_lower:
                    issues.append(f"Missing required section: '{section}'.")
                    recommendations.append(f"Ensure output includes '{section}'.")

        # Score calculation
        if not issues:
            score = 1.0
        elif len(issues) <= 1:
            score = 0.7
        elif len(issues) <= 3:
            score = 0.4
        else:
            score = 0.2

        passed = len(issues) == 0

        return ValidationResult(
            passed=passed,
            score=score,
            issues=issues,
            recommendations=recommendations,
        )
