from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.solution_blueprint import SolutionBlueprint
from core.project_estimate import ProjectEstimate

LOGGER = logging.getLogger(__name__)


class EstimationEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_estimate_id(self) -> str:
        est_id = f"EST-{self._next_id:04d}"
        self._next_id += 1
        return est_id

    def classify_complexity(self, blueprint: SolutionBlueprint) -> str:
        if blueprint is None:
            return "Medium"
            
        rca = getattr(blueprint, "root_cause_analysis", {})
        symptoms = rca.get("symptoms", [])
        business_constraints = rca.get("business_constraints", [])
        technical_constraints = rca.get("technical_constraints", [])
        operational_constraints = rca.get("operational_constraints", [])
        capabilities = getattr(blueprint, "required_capabilities", [])
        
        score = (
            len(symptoms)
            + len(business_constraints)
            + len(technical_constraints)
            + len(operational_constraints)
            + len(capabilities)
        )
        
        if score >= 9:
            return "Enterprise"
        elif score >= 7:
            return "Very High"
        elif score >= 5:
            return "High"
        elif score >= 3:
            return "Medium"
        elif score >= 2:
            return "Low"
        else:
            return "Very Low"

    def recommend_delivery_strategy(self, complexity: str) -> str:
        strategies = {
            "Very Low": "Kanban (Justification: Simple task layout requires minimal workflow overhead.)",
            "Low": "Kanban (Justification: Low complexity is best suited for visual task boards.)",
            "Medium": "Scrum (Justification: Standard development fits repeatable 2-week iterations.)",
            "High": "Scrum (Justification: High cross-functional coordination requires active backlog grooming.)",
            "Very High": "Hybrid (Justification: Blending Scrum with Waterfall phases to handle dependencies.)",
            "Enterprise": "Waterfall (Justification: Strict compliance and vast deployment bounds require phase-gated execution.)",
        }
        return strategies.get(complexity, "Agile")

    def calculate_risk_buffer(self, blueprint: SolutionBlueprint) -> dict[str, Any]:
        complexity = self.classify_complexity(blueprint)
        
        # Buffer percentages
        percentages = {
            "Very Low": 0.05,
            "Low": 0.10,
            "Medium": 0.15,
            "High": 0.20,
            "Very High": 0.25,
            "Enterprise": 0.30,
        }
        pct = percentages.get(complexity, 0.15)
        
        # Calculate expected duration to apply buffer
        expected_duration = self._get_expected_duration(complexity)
        added_duration = round(expected_duration * pct, 2)
        
        return {
            "percentage": pct * 100,
            "additional_duration_weeks": added_duration,
            "justification": f"Contingency buffer matching {complexity} project parameters."
        }

    def calculate_confidence(self, blueprint: SolutionBlueprint) -> float:
        if blueprint is None:
            return 0.0
        # Calculate based on blueprint confidence score
        bp_score = getattr(blueprint, "confidence_score", 0.5)
        score = bp_score * 0.9
        return round(score, 2)

    def generate_milestones(self, blueprint: SolutionBlueprint) -> list[str]:
        complexity = self.classify_complexity(blueprint)
        milestones = ["Discovery Complete", "Architecture Approved"]
        
        if complexity not in ["Very Low", "Low"]:
            milestones.append("Prototype Approved")
            
        milestones.extend([
            "MVP Delivered",
            "User Acceptance Testing",
            "Production Deployment",
            "Project Closure"
        ])
        return milestones

    def _get_expected_duration(self, complexity: str) -> float:
        durations = {
            "Very Low": 1.0,
            "Low": 2.0,
            "Medium": 4.0,
            "High": 8.0,
            "Very High": 12.0,
            "Enterprise": 24.0,
        }
        return durations.get(complexity, 4.0)

    def _get_expected_effort(self, complexity: str) -> float:
        efforts = {
            "Very Low": 40.0,
            "Low": 80.0,
            "Medium": 160.0,
            "High": 320.0,
            "Very High": 480.0,
            "Enterprise": 960.0,
        }
        return efforts.get(complexity, 160.0)

    def estimate(self, blueprint: SolutionBlueprint) -> ProjectEstimate:
        return self.generate_estimate(blueprint)

    def generate_estimate(self, blueprint: SolutionBlueprint) -> ProjectEstimate:
        if blueprint is None:
            raise ValueError("Solution blueprint is required.")
            
        blueprint_id = getattr(blueprint, "blueprint_id", "UNKNOWN")
        opportunity_id = getattr(blueprint, "opportunity_id", None)
        estimate_id = self._generate_estimate_id()
        
        LOGGER.info("object_id=%s action=generate_estimate actor=system status=DRAFT", estimate_id)

        # 1. Gather properties
        client_summary = getattr(blueprint, "client_summary", "")
        recommended_solution = getattr(blueprint, "recommended_solution", {})
        solution_summary = recommended_solution.get("description", "Scoped blueprint solution.")
        
        required_departments = getattr(blueprint, "required_departments", [])
        required_skills = getattr(blueprint, "required_skills", [])
        required_capabilities = getattr(blueprint, "required_capabilities", [])

        # 2. Complexity & Strategy
        complexity = self.classify_complexity(blueprint)
        delivery_strategy = self.recommend_delivery_strategy(complexity)

        # 3. Calculate Ranges
        expected_duration = self._get_expected_duration(complexity)
        expected_effort = self._get_expected_effort(complexity)

        best_case_duration = round(expected_duration * 0.75, 2)
        worst_case_duration = round(expected_duration * 1.5, 2)

        best_case_effort = round(expected_effort * 0.75, 2)
        worst_case_effort = round(expected_effort * 1.5, 2)

        estimated_duration = f"Expected: {expected_duration} weeks (Range: {best_case_duration}-{worst_case_duration} weeks)"
        estimated_effort = f"Expected: {expected_effort} person-hours (Range: {best_case_effort}-{worst_case_effort} hours)"

        # 4. Resource requirements
        team_size = 2 if complexity in ["Very Low", "Low"] else (4 if complexity in ["Medium", "High"] else 8)
        resource_requirements = {
            "estimated_team_size": team_size,
            "executive_roles": ["Chief of Staff", "Startup CTO"] if complexity != "Very Low" else ["Chief of Staff"],
            "specialists": ["QA Tester"] if complexity in ["High", "Very High", "Enterprise"] else [],
            "external_dependencies": []
        }

        # 5. Risk Buffer & Milestones
        risk_buffer = self.calculate_risk_buffer(blueprint)
        major_milestones = self.generate_milestones(blueprint)

        # 6. Metadata summaries
        critical_dependencies = getattr(blueprint, "dependencies", [])
        key_assumptions = getattr(blueprint, "assumptions", [])
        known_constraints = []
        
        rca = getattr(blueprint, "root_cause_analysis", {})
        for key in ["business_constraints", "operational_constraints", "technical_constraints"]:
            known_constraints.extend(rca.get(key, []))

        confidence_score = self.calculate_confidence(blueprint)

        estimate = ProjectEstimate(
            estimate_id=estimate_id,
            blueprint_id=blueprint_id,
            client_summary=client_summary,
            solution_summary=solution_summary,
            delivery_complexity=complexity,
            estimated_duration=estimated_duration,
            estimated_effort=estimated_effort,
            best_case_duration=best_case_duration,
            expected_duration=expected_duration,
            worst_case_duration=worst_case_duration,
            best_case_effort=best_case_effort,
            expected_effort=expected_effort,
            worst_case_effort=worst_case_effort,
            required_departments=required_departments,
            required_executive_roles=resource_requirements["executive_roles"],
            required_skills=required_skills,
            required_capabilities=required_capabilities,
            resource_requirements=resource_requirements,
            delivery_strategy=delivery_strategy,
            major_milestones=major_milestones,
            critical_dependencies=critical_dependencies,
            risk_buffer=risk_buffer,
            key_assumptions=key_assumptions,
            known_constraints=known_constraints,
            confidence_score=confidence_score,
            executive_notes=f"Estimation generated for blueprint {blueprint_id}. Proceed to commercial pricing.",
        )

        LOGGER.info(
            "object_id=%s action=generate_estimate actor=system status=READY confidence=%s",
            estimate_id,
            estimate.confidence_score,
        )
        return estimate
