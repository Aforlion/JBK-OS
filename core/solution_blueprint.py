from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class SolutionBlueprint:
    def __init__(
        self,
        blueprint_id: str,
        opportunity_id: str | None,
        discovery_plan_id: str,
        client_summary: str,
        business_problem: str,
        root_cause_analysis: dict[str, Any],
        business_objectives: list[str],
        proposed_solution_options: list[dict[str, Any]],
        recommended_solution: dict[str, Any],
        business_benefits: list[str],
        technical_considerations: list[str],
        required_capabilities: list[str],
        required_skills: list[str],
        required_departments: list[str],
        estimated_complexity: str,
        risks: list[str],
        assumptions: list[str],
        dependencies: list[str],
        success_metrics: list[str],
        executive_recommendation: str,
        confidence_score: float,
        created_at: str | None = None,
    ) -> None:
        self.blueprint_id = blueprint_id
        self.opportunity_id = opportunity_id
        self.discovery_plan_id = discovery_plan_id
        self.client_summary = client_summary or ""
        self.business_problem = business_problem or ""
        self.root_cause_analysis = root_cause_analysis or {}
        self.business_objectives = business_objectives or []
        self.proposed_solution_options = proposed_solution_options or []
        self.recommended_solution = recommended_solution or {}
        self.business_benefits = business_benefits or []
        self.technical_considerations = technical_considerations or []
        self.required_capabilities = required_capabilities or []
        self.required_skills = required_skills or []
        self.required_departments = required_departments or []
        self.estimated_complexity = estimated_complexity or "Medium"
        self.risks = risks or []
        self.assumptions = assumptions or []
        self.dependencies = dependencies or []
        self.success_metrics = success_metrics or []
        self.executive_recommendation = executive_recommendation or ""
        self.confidence_score = float(confidence_score)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "opportunity_id": self.opportunity_id,
            "discovery_plan_id": self.discovery_plan_id,
            "recommended_solution_title": self.recommended_solution.get("title", "N/A"),
            "estimated_complexity": self.estimated_complexity,
            "confidence_score": self.confidence_score,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "opportunity_id": self.opportunity_id,
            "discovery_plan_id": self.discovery_plan_id,
            "client_summary": self.client_summary,
            "business_problem": self.business_problem,
            "root_cause_analysis": dict(self.root_cause_analysis),
            "business_objectives": list(self.business_objectives),
            "proposed_solution_options": [dict(opt) for opt in self.proposed_solution_options],
            "recommended_solution": dict(self.recommended_solution),
            "business_benefits": list(self.business_benefits),
            "technical_considerations": list(self.technical_considerations),
            "required_capabilities": list(self.required_capabilities),
            "required_skills": list(self.required_skills),
            "required_departments": list(self.required_departments),
            "estimated_complexity": self.estimated_complexity,
            "risks": list(self.risks),
            "assumptions": list(self.assumptions),
            "dependencies": list(self.dependencies),
            "success_metrics": list(self.success_metrics),
            "executive_recommendation": self.executive_recommendation,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at,
        }
