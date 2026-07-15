from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.opportunity_brief import OpportunityBrief
from core.discovery_plan import DiscoveryPlan

LOGGER = logging.getLogger(__name__)


class DiscoveryConversationEngine:
    def __init__(self) -> None:
        self._next_id = 1
        
        # Priority mapping
        self.category_priorities = {
            "Business": 1,
            "Current Process": 1,
            "Success Criteria": 1,
            "People": 2,
            "Operations": 2,
            "Budget": 2,
            "Timeline": 2,
            "Technology": 3,
            "Risks": 3,
            "Compliance": 3,
            "Future Growth": 3,
        }

    def _generate_discovery_id(self) -> str:
        dsc_id = f"DSC-{self._next_id:04d}"
        self._next_id += 1
        return dsc_id

    def generate_plan(self, opportunity_brief: OpportunityBrief) -> DiscoveryPlan:
        if opportunity_brief is None:
            raise ValueError("Opportunity brief is required.")

        opp_id = getattr(opportunity_brief, "opportunity_id", None)
        discovery_id = self._generate_discovery_id()
        
        LOGGER.info("object_id=%s action=generate_plan actor=system status=DRAFT", discovery_id)

        domain = getattr(opportunity_brief, "business_domain", "General")
        problems = getattr(opportunity_brief, "business_problems", [])
        outcomes = getattr(opportunity_brief, "desired_outcomes", [])
        constraints = getattr(opportunity_brief, "known_constraints", [])
        missing_info = getattr(opportunity_brief, "missing_information", [])

        # 1. Objective Formulation
        if outcomes:
            conversation_objective = f"Verify and scope outcomes: {outcomes[0]}"
        else:
            conversation_objective = "Discover fundamental client business objectives and parameters."

        # 2. Information Already Known
        info_already_known = []
        if domain != "Unknown":
            info_already_known.append(f"Business Domain: {domain}")
        for p in problems:
            info_already_known.append(f"Problem: {p}")
        for o in outcomes:
            info_already_known.append(f"Outcome Goal: {o}")
        for c in constraints:
            info_already_known.append(f"Constraint: {c}")

        # 3. Information Still Required
        info_still_required = []
        for item in missing_info:
            info_still_required.append(item)
            
        # Add baseline required items if missing
        required_baselines = {
            "Success Criteria": "How success will be measured.",
            "Current Process": "Description of current process steps.",
            "Risks": "Possible organizational or technical risks.",
            "Compliance": "Required compliance rules or standards.",
            "Future Growth": "How the solution scales with future growth."
        }
        
        # Check if baselines are already answered in Outcomes/Constraints
        all_known_text = " ".join(info_already_known).lower()
        for cat, desc in required_baselines.items():
            cat_words = cat.lower().split()
            if not any(word in all_known_text for word in cat_words):
                info_still_required.append(desc)

        # 4. Generate Questions dynamically based on brief properties
        raw_questions = []
        
        # Template questions for all 11 categories
        # Tailored dynamically using domain and problems
        dynamic_questions_templates = {
            "Business": f"What is the primary business driver for this {domain} initiative?",
            "Current Process": "Can you describe the step-by-step current process that you are using today?",
            "Success Criteria": "What specific metrics or outcomes will define success for this initiative?",
            "People": "Who are the key users, coordinators, and stakeholders affected by this change?",
            "Operations": "How will this solution integrate into your day-to-day operations?",
            "Budget": "What is the budget or cost limitation for this project?",
            "Timeline": "Are there critical milestones or target dates we must align with?",
            "Technology": f"What existing technology systems must this {domain} solution integrate with?",
            "Risks": "What is the biggest operational or migration risk you foresee?",
            "Compliance": "Are there specific legal, industry, or security compliance rules we must follow?",
            "Future Growth": "How do you see this business capability scaling over the next 2-5 years?",
        }

        # Modify templates if we already know some of this information (ask validations instead of introductions)
        for cat, q_text in dynamic_questions_templates.items():
            cat_clean = cat.lower()
            
            # Check if this category's info is already known
            is_known = False
            if cat_clean == "budget" and not any("budget" in item.lower() for item in missing_info) and any("budget" in item.lower() for item in info_already_known):
                is_known = True
            elif cat_clean == "timeline" and not any("timeline" in item.lower() for item in missing_info) and any("timeline" in item.lower() for item in info_already_known):
                is_known = True
            elif cat_clean == "technology" and not any("technology" in item.lower() for item in missing_info) and any("technology" in item.lower() for item in info_already_known):
                is_known = True
                
            # If known, we can skip or ask validation. Let's skip to avoid asking questions whose answers are already known
            if is_known:
                continue

            # Prioritize
            priority = self.category_priorities.get(cat, 3)
            raw_questions.append({
                "question": q_text,
                "category": cat,
                "priority": priority
            })

        # 5. Prioritize Questions
        recommended_question_sequence = self.prioritize_questions(raw_questions)

        # 6. Completeness & Confidence Score
        discovery_completeness = self.calculate_completeness(opportunity_brief)
        confidence_score = getattr(opportunity_brief, "confidence_score", 0.5)

        # 7. Recommended Next Step
        recommended_next_step = self.recommend_next_step(discovery_completeness)

        plan = DiscoveryPlan(
            discovery_id=discovery_id,
            opportunity_id=opp_id,
            conversation_objective=conversation_objective,
            information_already_known=info_already_known,
            information_still_required=info_still_required,
            recommended_question_sequence=recommended_question_sequence,
            conversation_categories=list(self.category_priorities.keys()),
            discovery_completeness=discovery_completeness,
            confidence_score=confidence_score,
            recommended_next_step=recommended_next_step,
        )

        LOGGER.info(
            "object_id=%s action=generate_plan actor=system status=READY completeness=%s",
            discovery_id,
            plan.discovery_completeness,
        )
        return plan

    def prioritize_questions(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Sort questions: Priority 1 (highest/smallest number) first, then 2, then 3
        # Keep stable sort using python's built-in sorted
        return sorted(questions, key=lambda q: q.get("priority", 3))

    def calculate_completeness(self, opportunity_brief: OpportunityBrief) -> float:
        if opportunity_brief is None:
            return 0.0
            
        missing = getattr(opportunity_brief, "missing_information", [])
        # We check completeness based on how many missing items out of 4 default categories we have resolved
        # Standard categories: Budget, Timeline, Technology, Contact
        max_items = 4
        missing_count = len([m for m in missing if any(w in m.lower() for w in ["budget", "timeline", "technology", "contact"])])
        
        resolved_count = max(0, max_items - missing_count)
        completeness = resolved_count / max_items
        return round(completeness, 2)

    def recommend_next_step(self, completeness: float) -> str:
        if completeness >= 0.8:
            return "Scope Solution"
        elif completeness >= 0.5:
            return "Stakeholder Discovery Workshop"
        else:
            return "Discovery Call"
