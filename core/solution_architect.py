from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.discovery_plan import DiscoveryPlan
from core.solution_blueprint import SolutionBlueprint

LOGGER = logging.getLogger(__name__)


class SolutionArchitect:
    def __init__(self) -> None:
        self._next_id = 1
        
        # Evaluation criteria weights
        self.evaluation_criteria = [
            "Business Value",
            "Implementation Risk",
            "Cost Efficiency",
            "Time to Deliver",
            "Scalability",
            "Maintainability",
            "Operational Impact",
            "Customer Experience",
            "Strategic Alignment",
        ]

    def _generate_blueprint_id(self) -> str:
        blp_id = f"BLP-{self._next_id:04d}"
        self._next_id += 1
        return blp_id

    def calculate_confidence(self, discovery_plan: DiscoveryPlan) -> float:
        if discovery_plan is None:
            return 0.0
        completeness = getattr(discovery_plan, "discovery_completeness", 0.5)
        score = completeness * 0.9 + 0.1
        return round(score, 2)

    def evaluate_options(self, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Evaluate each option against the 9 criteria
        # For simplicity, assign mock scores based on option properties
        evaluated = []
        for opt in options:
            scores = {}
            total = 0.0
            complexity = opt.get("complexity", "Medium")
            
            # Simple heuristic scoring
            for criterion in self.evaluation_criteria:
                if criterion == "Scalability":
                    score = 5.0 if "platform" in opt.get("description", "").lower() else 3.0
                elif criterion == "Cost Efficiency":
                    score = 5.0 if "lean" in opt.get("description", "").lower() or "integrate" in opt.get("description", "").lower() else 2.5
                elif criterion == "Implementation Risk":
                    score = 4.5 if complexity == "Low" else (3.0 if complexity == "Medium" else 1.5)
                elif criterion == "Business Value":
                    score = 4.8 if complexity == "High" else 3.5
                else:
                    score = 4.0
                scores[criterion] = score
                total += score
                
            opt_copy = dict(opt)
            opt_copy["scores"] = scores
            opt_copy["overall_score"] = round(total / len(self.evaluation_criteria), 2)
            evaluated.append(opt_copy)
            
        return evaluated

    def recommend_solution(self, options: list[dict[str, Any]], evaluation: list[dict[str, Any]]) -> dict[str, Any]:
        if not evaluation:
            return {}
            
        # Select option with highest overall score
        sorted_eval = sorted(evaluation, key=lambda x: x.get("overall_score", 0.0), reverse=True)
        best = sorted_eval[0]
        
        alternatives = [x for x in sorted_eval[1:]]
        alt_titles = ", ".join(x.get("title", "Alternative") for x in alternatives)
        
        recommendation = {
            "title": best.get("title"),
            "description": best.get("description"),
            "overall_score": best.get("overall_score"),
            "why_selected": f"Selected {best.get('title')} due to high score in efficiency and strategic alignment.",
            "why_alternatives_rejected": f"Alternatives ({alt_titles}) were rejected due to high implementation risk or lack of long-term scalability.",
            "trade_offs": "Balancing initial capital costs against operational efficiency goals.",
            "executive_considerations": "Requires direct oversight from Technology Division during deployment."
        }
        return recommendation

    def design_solution(self, discovery_plan: DiscoveryPlan) -> SolutionBlueprint:
        return self.generate_blueprint(discovery_plan)

    def generate_blueprint(self, discovery_plan: DiscoveryPlan) -> SolutionBlueprint:
        if discovery_plan is None:
            raise ValueError("Discovery plan is required.")
            
        opp_id = getattr(discovery_plan, "opportunity_id", None)
        dsc_id = getattr(discovery_plan, "discovery_id", "UNKNOWN")
        blueprint_id = self._generate_blueprint_id()
        
        LOGGER.info("object_id=%s action=generate_blueprint actor=system status=DRAFT", blueprint_id)

        # 1. Gather inputs
        known_items = getattr(discovery_plan, "information_already_known", [])
        still_required = getattr(discovery_plan, "information_still_required", [])
        objective = getattr(discovery_plan, "conversation_objective", "Scoping")

        # 2. Extract Client Summary and Business Problems
        problems = [k.replace("Problem: ", "") for k in known_items if k.startswith("Problem: ")]
        outcomes = [k.replace("Outcome Goal: ", "") for k in known_items if k.startswith("Outcome Goal: ")]
        constraints = [k.replace("Constraint: ", "") for k in known_items if k.startswith("Constraint: ")]
        domain = "General"
        for k in known_items:
            if k.startswith("Business Domain: "):
                domain = k.replace("Business Domain: ", "")

        client_summary = f"Client request in {domain} domain targeting {objective} goals."
        business_problem = " | ".join(problems) if problems else "Unspecified business pain points."

        # 3. Root Cause Analysis
        symptoms = list(problems)
        root_problems = []
        business_constraints = []
        operational_constraints = []
        technical_constraints = []

        for p in problems:
            p_lower = p.lower()
            if "slow" in p_lower or "inefficient" in p_lower:
                root_problems.append("Outdated process orchestration or legacy pipelines")
            elif "fail" in p_lower or "error" in p_lower:
                root_problems.append("Fragile interface design or lack of exception safeguards")
            else:
                root_problems.append("Process friction or lack of automation tooling")

        for c in constraints:
            c_lower = c.lower()
            if "budget" in c_lower or "cost" in c_lower or "$" in c_lower:
                business_constraints.append(c)
            elif "deadline" in c_lower or "timeline" in c_lower or "weeks" in c_lower or "days" in c_lower:
                operational_constraints.append(c)
            else:
                technical_constraints.append(c)

        root_cause_analysis = {
            "symptoms": symptoms,
            "root_problems": list(set(root_problems)),
            "business_constraints": business_constraints,
            "operational_constraints": operational_constraints,
            "technical_constraints": technical_constraints,
        }

        # 4. Formulate Solution Options
        options = [
            {
                "title": f"Lean Integration & Process Optimization ({domain})",
                "description": "Optimize operations by integrating existing third-party SaaS platforms to minimize deployment overhead.",
                "benefits": ["Low risk", "Low cost", "Fast time to market"],
                "limitations": ["Vendor lock-in", "Limited customization capabilities"],
                "complexity": "Low",
                "risks": ["Third-party API changes"],
                "strategic_fit": "High fit for immediate cost optimization goals.",
                "long_term_value": "Medium"
            },
            {
                "title": f"Custom Scalable Platform ({domain})",
                "description": "Build a custom, modular platform utilizing JBK OS microservice layers to guarantee long-term scaling.",
                "benefits": ["High customization", "No licensing fees", "Fully owned IP"],
                "limitations": ["Higher capital investment", "Longer implementation timeline"],
                "complexity": "High",
                "risks": ["Technical integration complexity", "Staff training overhead"],
                "strategic_fit": "Perfect fit for long-term scalability targets.",
                "long_term_value": "High"
            }
        ]

        # 5. Evaluate and Recommend
        evaluation = self.evaluate_options(options)
        recommended_solution = self.recommend_solution(options, evaluation)

        # 6. Technical Considerations & Capabilities
        required_capabilities = ["AI Automation", "API Integration", "UX Design", "Security Review"]
        if domain == "Technology":
            required_capabilities.extend(["Web Development", "Data Migration"])
            
        required_skills = ["software-engineer", "process-optimizer", "security-architect"]
        required_departments = ["Technology", "Operations"]

        # 7. Metadata summaries
        risks = []
        for opt in options:
            risks.extend(opt.get("risks", []))
            
        assumptions = [
            "Client stakeholders will prioritize clarification interviews.",
            "Existing infrastructure has capacity to host the proposed architecture."
        ]
        dependencies = [
            "Access to client internal legacy API schemas."
        ]
        success_metrics = [
            "Reduction in operational error rate by 50%",
            "Improvement in system throughput by 30%"
        ]

        confidence_score = self.calculate_confidence(discovery_plan)

        blueprint = SolutionBlueprint(
            blueprint_id=blueprint_id,
            opportunity_id=opp_id,
            discovery_plan_id=dsc_id,
            client_summary=client_summary,
            business_problem=business_problem,
            root_cause_analysis=root_cause_analysis,
            business_objectives=outcomes,
            proposed_solution_options=evaluation,
            recommended_solution=recommended_solution,
            business_benefits=recommended_solution.get("benefits", ["Operational efficiency"]),
            technical_considerations=["Containerized deployment", "Rate-limiting security guards"],
            required_capabilities=required_capabilities,
            required_skills=required_skills,
            required_departments=required_departments,
            estimated_complexity="Medium",
            risks=list(set(risks)),
            assumptions=assumptions,
            dependencies=dependencies,
            success_metrics=success_metrics,
            executive_recommendation=recommended_solution.get("why_selected", ""),
            confidence_score=confidence_score,
        )

        LOGGER.info(
            "object_id=%s action=generate_blueprint actor=system status=READY confidence=%s",
            blueprint_id,
            blueprint.confidence_score,
        )
        return blueprint
