from __future__ import annotations

import re
from typing import Any
from datetime import datetime, timezone


class KPI:
    """A measurable business Key Performance Indicator.

    Every KPI must carry a measurement_method and target_value.
    """

    def __init__(
        self,
        kpi_id: str,
        name: str,
        description: str,
        baseline: str,
        target_value: str,
        unit: str,
        measurement_method: str,
        timeframe: str,
        owner_department: str,
        source_metric: str = "",
        created_at: str | None = None,
    ) -> None:
        if not kpi_id:
            raise ValueError("KPI ID is required.")
        if not name:
            raise ValueError("KPI name is required.")
        if not measurement_method:
            raise ValueError("KPI measurement_method is required.")
        if not target_value:
            raise ValueError("KPI target_value is required.")

        self.kpi_id = kpi_id
        self.name = name
        self.description = description or ""
        self.baseline = baseline or "To be established"
        self.target_value = target_value
        self.unit = unit or ""
        self.measurement_method = measurement_method
        self.timeframe = timeframe or "End of project"
        self.owner_department = owner_department or "Operations"
        self.source_metric = source_metric or ""
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "target_value": self.target_value,
            "unit": self.unit,
            "timeframe": self.timeframe,
            "owner_department": self.owner_department,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "description": self.description,
            "baseline": self.baseline,
            "target_value": self.target_value,
            "unit": self.unit,
            "measurement_method": self.measurement_method,
            "timeframe": self.timeframe,
            "owner_department": self.owner_department,
            "source_metric": self.source_metric,
            "created_at": self.created_at,
        }


class TransformationObjective:
    """A specific business outcome linked to one or more blueprint business goals."""

    def __init__(
        self,
        objective_id: str,
        title: str,
        description: str,
        linked_business_goals: list[str],
        owner_department: str,
        success_criteria: list[str],
        priority: str = "MEDIUM",
        created_at: str | None = None,
    ) -> None:
        if not objective_id:
            raise ValueError("Objective ID is required.")
        if not title:
            raise ValueError("Objective title is required.")
        if not linked_business_goals:
            raise ValueError("At least one linked business goal is required.")

        self.objective_id = objective_id
        self.title = title
        self.description = description or ""
        self.linked_business_goals = list(linked_business_goals)
        self.owner_department = owner_department or "Leadership"
        self.success_criteria = list(success_criteria or [])
        self.priority = (priority or "MEDIUM").upper()
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "owner_department": self.owner_department,
            "priority": self.priority,
            "linked_goal_count": len(self.linked_business_goals),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "description": self.description,
            "linked_business_goals": list(self.linked_business_goals),
            "owner_department": self.owner_department,
            "success_criteria": list(self.success_criteria),
            "priority": self.priority,
            "created_at": self.created_at,
        }


class ChangeImpact:
    """Department-level impact record describing how a department is affected by the transformation."""

    IMPACT_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})

    def __init__(
        self,
        impact_id: str,
        department: str,
        impact_level: str,
        affected_processes: list[str],
        headcount_affected: int,
        change_description: str,
        training_required: list[str],
        readiness_actions: list[str],
        created_at: str | None = None,
    ) -> None:
        if not impact_id:
            raise ValueError("Impact ID is required.")
        if not department:
            raise ValueError("Department is required.")

        normalized_level = (impact_level or "MEDIUM").upper()
        if normalized_level not in self.IMPACT_LEVELS:
            normalized_level = "MEDIUM"

        self.impact_id = impact_id
        self.department = department
        self.impact_level = normalized_level
        self.affected_processes = list(affected_processes or [])
        self.headcount_affected = max(0, int(headcount_affected or 0))
        self.change_description = change_description or ""
        self.training_required = list(training_required or [])
        self.readiness_actions = list(readiness_actions or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "impact_id": self.impact_id,
            "department": self.department,
            "impact_level": self.impact_level,
            "headcount_affected": self.headcount_affected,
            "process_count": len(self.affected_processes),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "impact_id": self.impact_id,
            "department": self.department,
            "impact_level": self.impact_level,
            "affected_processes": list(self.affected_processes),
            "headcount_affected": self.headcount_affected,
            "change_description": self.change_description,
            "training_required": list(self.training_required),
            "readiness_actions": list(self.readiness_actions),
            "created_at": self.created_at,
        }


class AdoptionPhase:
    """A time-boxed adoption stage in the transformation rollout."""

    def __init__(
        self,
        phase_id: str,
        name: str,
        description: str,
        sequence: int,
        duration_weeks: float,
        scope: str,
        key_activities: list[str],
        success_gate: str,
        responsible_parties: list[str],
        created_at: str | None = None,
    ) -> None:
        if not phase_id:
            raise ValueError("Phase ID is required.")
        if not name:
            raise ValueError("Phase name is required.")

        self.phase_id = phase_id
        self.name = name
        self.description = description or ""
        self.sequence = int(sequence or 1)
        self.duration_weeks = float(duration_weeks or 2.0)
        self.scope = scope or "To be defined"
        self.key_activities = list(key_activities or [])
        self.success_gate = success_gate or "Stakeholder sign-off"
        self.responsible_parties = list(responsible_parties or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "sequence": self.sequence,
            "duration_weeks": self.duration_weeks,
            "scope": self.scope,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,
            "sequence": self.sequence,
            "duration_weeks": self.duration_weeks,
            "scope": self.scope,
            "key_activities": list(self.key_activities),
            "success_gate": self.success_gate,
            "responsible_parties": list(self.responsible_parties),
            "created_at": self.created_at,
        }


class BusinessTransformationPlan:
    """Top-level transformation plan converting an approved solution into a measurable
    business change roadmap.

    ID format: BTP-0001
    """

    def __init__(
        self,
        plan_id: str,
        blueprint_id: str,
        client: str,
        current_state_assessment: dict[str, Any],
        future_state_vision: dict[str, Any],
        transformation_objectives: list[TransformationObjective],
        department_impact_analysis: list[ChangeImpact],
        process_changes: list[dict[str, Any]],
        change_management_plan: dict[str, Any],
        training_plan: dict[str, Any],
        adoption_strategy: list[AdoptionPhase],
        kpi_dashboard: list[KPI],
        success_metrics: list[str],
        risk_register: list[dict[str, Any]],
        executive_recommendations: list[str],
        warnings: list[str] | None = None,
        created_at: str | None = None,
    ) -> None:
        if not plan_id:
            raise ValueError("Plan ID is required.")
        if not blueprint_id:
            raise ValueError("Blueprint ID is required.")
        if not client:
            raise ValueError("Client is required.")

        self.plan_id = plan_id
        self.blueprint_id = blueprint_id
        self.client = client
        self.current_state_assessment = dict(current_state_assessment or {})
        self.future_state_vision = dict(future_state_vision or {})
        self.transformation_objectives = list(transformation_objectives or [])
        self.department_impact_analysis = list(department_impact_analysis or [])
        self.process_changes = list(process_changes or [])
        self.change_management_plan = dict(change_management_plan or {})
        self.training_plan = dict(training_plan or {})
        self.adoption_strategy = list(adoption_strategy or [])
        self.kpi_dashboard = list(kpi_dashboard or [])
        self.success_metrics = list(success_metrics or [])
        self.risk_register = list(risk_register or [])
        self.executive_recommendations = list(executive_recommendations or [])
        self.warnings = list(warnings or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "blueprint_id": self.blueprint_id,
            "client": self.client,
            "objective_count": len(self.transformation_objectives),
            "kpi_count": len(self.kpi_dashboard),
            "department_count": len(self.department_impact_analysis),
            "adoption_phase_count": len(self.adoption_strategy),
            "risk_count": len(self.risk_register),
            "process_change_count": len(self.process_changes),
            "warning_count": len(self.warnings),
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "blueprint_id": self.blueprint_id,
            "client": self.client,
            "current_state_assessment": dict(self.current_state_assessment),
            "future_state_vision": dict(self.future_state_vision),
            "transformation_objectives": [o.to_dict() for o in self.transformation_objectives],
            "department_impact_analysis": [d.to_dict() for d in self.department_impact_analysis],
            "process_changes": list(self.process_changes),
            "change_management_plan": dict(self.change_management_plan),
            "training_plan": dict(self.training_plan),
            "adoption_strategy": [p.to_dict() for p in self.adoption_strategy],
            "kpi_dashboard": [k.to_dict() for k in self.kpi_dashboard],
            "success_metrics": list(self.success_metrics),
            "risk_register": list(self.risk_register),
            "executive_recommendations": list(self.executive_recommendations),
            "warnings": list(self.warnings),
            "summary": self.summary(),
            "created_at": self.created_at,
        }
