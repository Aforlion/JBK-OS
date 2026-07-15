from __future__ import annotations

import re
import uuid
import logging
from typing import Any

from core.opportunity_brief import OpportunityBrief, OpportunityStatus

LOGGER = logging.getLogger(__name__)


class OpportunityIntakeEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_opportunity_id(self) -> str:
        opp_id = f"OPP-{self._next_id:04d}"
        self._next_id += 1
        return opp_id

    def intake(self, client_request_text: str) -> OpportunityBrief:
        if client_request_text is None:
            raise ValueError("Client request text cannot be None.")
            
        request_clean = client_request_text.strip()
        if not request_clean:
            raise ValueError("Client request text cannot be empty.")

        opportunity_id = self._generate_opportunity_id()
        LOGGER.info("object_id=%s action=intake actor=system status=DRAFT", opportunity_id)

        # 1. Detect Business Domain
        text_lower = request_clean.lower()
        if any(w in text_lower for w in ["database", "server", "api", "backend", "develop", "migration", "host", "cloud", "software"]):
            business_domain = "Technology"
        elif any(w in text_lower for w in ["marketing", "sales", "funnel", "campaign", "conversion", "growth"]):
            business_domain = "Marketing"
        elif any(w in text_lower for w in ["process", "flow", "efficiency", "automation", "pipeline", "workflow", "optimization"]):
            business_domain = "Operations"
        else:
            business_domain = "General"

        # Helper to split text into sentences
        sentences = [s.strip() for s in re.split(r'[.!?\n]', request_clean) if s.strip()]

        # 2. Extract Business Problems
        problem_keywords = ["issue", "problem", "error", "fail", "slow", "leak", "down", "break", "unable", "struggle", "bottleneck", "lack"]
        business_problems = []
        for s in sentences:
            if any(w in s.lower() for w in problem_keywords):
                business_problems.append(s)
        if not business_problems:
            business_problems.append("Unstructured client request requires analysis for specific pain points.")

        # 3. Extract Desired Outcomes
        outcome_keywords = ["want", "need", "goal", "aim", "wish", "hope", "outcome", "desire", "deliver", "implement", "enable", "should support"]
        desired_outcomes = []
        for s in sentences:
            if any(w in s.lower() for w in outcome_keywords):
                desired_outcomes.append(s)

        # 4. Extract Known Constraints
        constraint_keywords = ["must", "limit", "budget", "deadline", "cannot", "restrict", "days", "weeks", "schedule", "cost", "only support"]
        known_constraints = []
        for s in sentences:
            if any(w in s.lower() for w in constraint_keywords):
                known_constraints.append(s)

        # 5. Identify Missing Information & Questions
        missing_information = []
        recommended_next_questions = []

        if not any(w in text_lower for w in ["budget", "cost", "$", "usd"]):
            missing_information.append("Budget or cost limits are not specified.")
            recommended_next_questions.append("What is your allocated budget for this initiative?")

        if not any(w in text_lower for w in ["deadline", "timeline", "by", "weeks", "days", "months", "schedule"]):
            missing_information.append("Project timeline or deadline is not specified.")
            recommended_next_questions.append("What is your desired delivery timeline or target deadline?")

        if not any(w in text_lower for w in ["technology", "stack", "python", "node", "database", "postgres", "mysql", "react", "nextjs", "aws"]):
            missing_information.append("Preferred technology stack is not specified.")
            recommended_next_questions.append("Do you have a preferred technology stack or architecture constraints?")

        if not any(w in text_lower for w in ["contact", "email", "phone", "who", "stakeholder", "decision maker", "representative"]):
            missing_information.append("Stakeholder contact information is not specified.")
            recommended_next_questions.append("Who is the primary point of contact and key decision maker for this project?")

        # 6. Complexity Rating
        complexity_metric = len(business_problems) + len(known_constraints)
        if complexity_metric > 4:
            complexity_rating = "High"
        elif complexity_metric >= 2:
            complexity_rating = "Medium"
        else:
            complexity_rating = "Low"

        # 7. Confidence Score
        confidence_score = max(0.0, 1.0 - (len(missing_information) * 0.2))
        confidence_score = round(confidence_score, 2)

        # 8. Next Step & Status
        if confidence_score < 0.6:
            status = OpportunityStatus.INSUFFICIENT_INFORMATION
            recommended_next_step = "Clarification Interview"
        else:
            status = OpportunityStatus.ANALYZED
            recommended_next_step = "Technical Scoping"
            
        if not missing_information:
            recommended_next_step = "Generate Proposal"

        brief = OpportunityBrief(
            opportunity_id=opportunity_id,
            client_request_text=request_clean,
            business_domain=business_domain,
            business_problems=business_problems,
            desired_outcomes=desired_outcomes,
            known_constraints=known_constraints,
            missing_information=missing_information,
            recommended_next_questions=recommended_next_questions,
            complexity_rating=complexity_rating,
            confidence_score=confidence_score,
            recommended_next_step=recommended_next_step,
            status=status,
        )

        LOGGER.info(
            "object_id=%s action=intake actor=system status=%s confidence=%s",
            opportunity_id,
            brief.status.value,
            brief.confidence_score,
        )
        return brief
