from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class ProjectEstimate:
    def __init__(
        self,
        estimate_id: str,
        blueprint_id: str,
        client_summary: str,
        solution_summary: str,
        delivery_complexity: str,
        estimated_duration: str,
        estimated_effort: str,
        best_case_duration: float,
        expected_duration: float,
        worst_case_duration: float,
        best_case_effort: float,
        expected_effort: float,
        worst_case_effort: float,
        required_departments: list[str],
        required_executive_roles: list[str],
        required_skills: list[str],
        required_capabilities: list[str],
        resource_requirements: dict[str, Any],
        delivery_strategy: str,
        major_milestones: list[str],
        critical_dependencies: list[str],
        risk_buffer: dict[str, Any],
        key_assumptions: list[str],
        known_constraints: list[str],
        confidence_score: float,
        executive_notes: str,
        created_at: str | None = None,
    ) -> None:
        self.estimate_id = estimate_id
        self.blueprint_id = blueprint_id
        self.client_summary = client_summary or ""
        self.solution_summary = solution_summary or ""
        self.delivery_complexity = delivery_complexity or "Medium"
        self.estimated_duration = estimated_duration or ""
        self.estimated_effort = estimated_effort or ""
        self.best_case_duration = float(best_case_duration)
        self.expected_duration = float(expected_duration)
        self.worst_case_duration = float(worst_case_duration)
        self.best_case_effort = float(best_case_effort)
        self.expected_effort = float(expected_effort)
        self.worst_case_effort = float(worst_case_effort)
        self.required_departments = required_departments or []
        self.required_executive_roles = required_executive_roles or []
        self.required_skills = required_skills or []
        self.required_capabilities = required_capabilities or []
        self.resource_requirements = resource_requirements or {}
        self.delivery_strategy = delivery_strategy or "Agile"
        self.major_milestones = major_milestones or []
        self.critical_dependencies = critical_dependencies or []
        self.risk_buffer = risk_buffer or {}
        self.key_assumptions = key_assumptions or []
        self.known_constraints = known_constraints or []
        self.confidence_score = float(confidence_score)
        self.executive_notes = executive_notes or ""
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "estimate_id": self.estimate_id,
            "blueprint_id": self.blueprint_id,
            "delivery_complexity": self.delivery_complexity,
            "expected_duration_weeks": self.expected_duration,
            "expected_effort_hours": self.expected_effort,
            "confidence_score": self.confidence_score,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimate_id": self.estimate_id,
            "blueprint_id": self.blueprint_id,
            "client_summary": self.client_summary,
            "solution_summary": self.solution_summary,
            "delivery_complexity": self.delivery_complexity,
            "estimated_duration": self.estimated_duration,
            "estimated_effort": self.estimated_effort,
            "best_case_duration": self.best_case_duration,
            "expected_duration": self.expected_duration,
            "worst_case_duration": self.worst_case_duration,
            "best_case_effort": self.best_case_effort,
            "expected_effort": self.expected_effort,
            "worst_case_effort": self.worst_case_effort,
            "required_departments": list(self.required_departments),
            "required_executive_roles": list(self.required_executive_roles),
            "required_skills": list(self.required_skills),
            "required_capabilities": list(self.required_capabilities),
            "resource_requirements": dict(self.resource_requirements),
            "delivery_strategy": self.delivery_strategy,
            "major_milestones": list(self.major_milestones),
            "critical_dependencies": list(self.critical_dependencies),
            "risk_buffer": dict(self.risk_buffer),
            "key_assumptions": list(self.key_assumptions),
            "known_constraints": list(self.known_constraints),
            "confidence_score": self.confidence_score,
            "executive_notes": self.executive_notes,
            "created_at": self.created_at,
        }
