from __future__ import annotations

from typing import Any

REQUIREMENT_CATEGORIES = (
    "KERNEL",
    "ARCHITECTURE",
    "GOVERNANCE",
    "OPERATIONS",
    "INTELLIGENCE",
    "AI",
    "SECURITY",
    "DEPLOYMENT",
    "RECOVERY",
    "INTEGRATIONS",
    "DOCUMENTATION",
    "TESTING",
)

REQUIREMENT_STATUSES = ("PASSED", "WARNING", "BLOCKER", "SKIPPED")


class CertificationRequirement:
    """Represents a standard requirement audited during production readiness checks.

    BR-056-009: Production blockers must include remediation guidance.
    BR-056-007: Serializable.
    """

    def __init__(
        self,
        req_id: str,
        category: str,
        title: str,
        description: str,
        status: str = "PASSED",
        remediation_guidance: str = "",
    ) -> None:
        if category not in REQUIREMENT_CATEGORIES:
            raise ValueError(f"Invalid category: '{category}'. Must be one of {REQUIREMENT_CATEGORIES}")
        if status not in REQUIREMENT_STATUSES:
            raise ValueError(f"Invalid status: '{status}'. Must be one of {REQUIREMENT_STATUSES}")
        if status == "BLOCKER" and not remediation_guidance:
            raise ValueError("Blockers must carry remediation guidance (BR-056-009).")

        self.req_id = req_id
        self.category = category
        self.title = title
        self.description = description
        self.status = status
        self.remediation_guidance = remediation_guidance

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "remediation_guidance": self.remediation_guidance,
        }
