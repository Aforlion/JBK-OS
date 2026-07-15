from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone
import uuid
import logging

LOGGER = logging.getLogger(__name__)


class PlanningStatus(str, Enum):
    CREATED = "CREATED"
    ANALYZED = "ANALYZED"
    READY = "READY"
    FAILED = "FAILED"


class ExecutionPlan:
    def __init__(
        self,
        plan_id: str,
        work_order_id: str,
        recommended_skill_id: str | None,
        execution_engine: str | None,
        confidence_score: float,
        reasoning: str,
        alternative_skills: list[str],
        created_at: str | None = None,
        status: PlanningStatus | str = PlanningStatus.CREATED,
    ) -> None:
        self.plan_id = plan_id
        self.work_order_id = work_order_id
        self.recommended_skill_id = recommended_skill_id
        self.execution_engine = execution_engine
        self.confidence_score = confidence_score
        self.reasoning = reasoning
        self.alternative_skills = alternative_skills or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.status = (
            status if isinstance(status, PlanningStatus) else PlanningStatus(status)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "work_order_id": self.work_order_id,
            "recommended_skill_id": self.recommended_skill_id,
            "confidence_score": self.confidence_score,
            "status": self.status.value,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "work_order_id": self.work_order_id,
            "recommended_skill_id": self.recommended_skill_id,
            "execution_engine": self.execution_engine,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "alternative_skills": list(self.alternative_skills),
            "created_at": self.created_at,
            "status": self.status.value,
        }


class ExecutionPlanner:
    def __init__(self, skill_registry: Any) -> None:
        if skill_registry is None:
            raise ValueError("Skill Registry is required.")
        self.skill_registry = skill_registry
        self.status = PlanningStatus.CREATED
        self.last_capabilities: list[str] = []
        self.last_candidates: list[Any] = []
        self.last_plan: ExecutionPlan | None = None
        self._next_id = 1

    def _generate_plan_id(self) -> str:
        plan_id = f"PLN-{self._next_id:04d}"
        self._next_id += 1
        return plan_id

    def analyze(self, work_order: Any) -> list[str]:
        if work_order is None:
            raise ValueError("Work order is required.")
        
        self.status = PlanningStatus.ANALYZED
        self.last_capabilities = self.identify_capabilities(work_order)
        LOGGER.info(
            "object_id=%s action=analyze actor=system status=ANALYZED capabilities=%s",
            getattr(work_order, "id", "UNKNOWN"),
            self.last_capabilities,
        )
        return self.last_capabilities

    def identify_capabilities(self, work_order: Any) -> list[str]:
        if work_order is None:
            return []
        
        title = getattr(work_order, "title", "").lower()
        objective = getattr(work_order, "objective", "").lower()

        # Collect all capabilities registered in skill registry
        known_caps = set()
        for skill in self.skill_registry.list_skills():
            for cap in getattr(skill, "capabilities", []):
                known_caps.add(cap.lower())

        matched = []
        for cap in known_caps:
            if cap in title or cap in objective:
                matched.append(cap)
        return list(set(matched))

    def discover_candidates(self, capabilities: list[str]) -> list[Any]:
        if not capabilities:
            return []
        
        candidates = []
        for cap in capabilities:
            candidates.extend(self.skill_registry.find_by_capability(cap))
            
        # Ensure uniqueness by id
        seen = set()
        unique_candidates = []
        for s in candidates:
            s_id = getattr(s, "skill_id", None) or getattr(s, "id", None)
            if s_id and s_id not in seen:
                seen.add(s_id)
                unique_candidates.append(s)
                
        self.last_candidates = unique_candidates
        return unique_candidates

    def evaluate_candidates(self, candidates: list[Any]) -> list[Any]:
        # BR-0020: Only AVAILABLE skills may be recommended
        available_candidates = [
            s
            for s in candidates
            if getattr(getattr(s, "status", None), "value", getattr(s, "status", None)) == "AVAILABLE"
        ]

        if not available_candidates or not self.last_capabilities:
            return []

        # BR-0022: Rank recommendations by capability overlap size
        req_caps_set = set(self.last_capabilities)
        
        def score_skill(skill: Any) -> int:
            skill_caps = set(getattr(skill, "capabilities", []))
            return len(skill_caps.intersection(req_caps_set))

        ranked = sorted(available_candidates, key=score_skill, reverse=True)
        return ranked

    def generate_plan(self, work_order: Any) -> ExecutionPlan:
        if work_order is None:
            raise ValueError("Work order is required.")
        
        work_order_id = getattr(work_order, "id", None)
        if not work_order_id:
            raise ValueError("Work order must have a valid ID.")

        plan_id = self._generate_plan_id()
        created_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Analyze
        capabilities = self.analyze(work_order)
        if not capabilities:
            self.status = PlanningStatus.FAILED
            self.last_plan = ExecutionPlan(
                plan_id=plan_id,
                work_order_id=work_order_id,
                recommended_skill_id=None,
                execution_engine=None,
                confidence_score=0.0,
                reasoning="No capabilities identified from work order description.",
                alternative_skills=[],
                created_at=created_at,
                status=PlanningStatus.FAILED,
            )
            return self.last_plan

        # Step 2: Discover
        candidates = self.discover_candidates(capabilities)

        # Step 3: Evaluate
        ranked_candidates = self.evaluate_candidates(candidates)

        if not ranked_candidates:
            # BR-0023: If no suitable skill exists, planning fails gracefully
            self.status = PlanningStatus.FAILED
            self.last_plan = ExecutionPlan(
                plan_id=plan_id,
                work_order_id=work_order_id,
                recommended_skill_id=None,
                execution_engine=None,
                confidence_score=0.0,
                reasoning="No suitable AVAILABLE candidate skills discovered.",
                alternative_skills=[],
                created_at=created_at,
                status=PlanningStatus.FAILED,
            )
            return self.last_plan

        # Select best candidate
        best_skill = ranked_candidates[0]
        alternative_skills = [
            getattr(s, "skill_id", None) or getattr(s, "id", None)
            for s in ranked_candidates[1:]
        ]
        alternative_skills = [s_id for s_id in alternative_skills if s_id]

        # Score confidence
        best_caps = set(getattr(best_skill, "capabilities", []))
        req_caps = set(capabilities)
        overlap = len(best_caps.intersection(req_caps))
        confidence_score = round(overlap / len(req_caps), 2) if req_caps else 1.0

        self.status = PlanningStatus.READY
        self.last_plan = ExecutionPlan(
            plan_id=plan_id,
            work_order_id=work_order_id,
            recommended_skill_id=best_skill.skill_id,
            execution_engine=best_skill.execution_engine,
            confidence_score=confidence_score,
            reasoning=f"Matched capability overlap of size {overlap} using AVAILABLE skill: {best_skill.name}.",
            alternative_skills=alternative_skills,
            created_at=created_at,
            status=PlanningStatus.READY,
        )
        return self.last_plan

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "last_capabilities_count": len(self.last_capabilities),
            "last_candidates_count": len(self.last_candidates),
            "last_plan_id": self.last_plan.plan_id if self.last_plan else None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "last_capabilities": list(self.last_capabilities),
            "last_plan": self.last_plan.to_dict() if self.last_plan else None,
            "summary": self.summary(),
        }
