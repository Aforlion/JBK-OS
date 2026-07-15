from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.delivery_plan import DeliveryPlan

LOGGER = logging.getLogger(__name__)


class DeliveryPlanningEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_delivery_plan_id(self) -> str:
        dpl_id = f"DPL-{self._next_id:04d}"
        self._next_id += 1
        return dpl_id

    def recommend_capabilities(self, stream_title: str) -> list[str]:
        title_lower = stream_title.lower()
        if "technology" in title_lower or "tech" in title_lower:
            return ["Web Development", "API Integration", "Data Migration"]
        elif "operations" in title_lower or "ops" in title_lower:
            return ["Business Process Design", "Training", "Documentation"]
        elif "compliance" in title_lower or "security" in title_lower:
            return ["Security Review"]
        else:
            return ["AI Automation"]

    def generate_phases(self, project_details: dict[str, Any]) -> list[dict[str, Any]]:
        complexity = project_details.get("complexity", "Medium").lower()
        
        if complexity in ["very low", "low"]:
            return [
                {
                    "title": "Design & Implementation",
                    "description": "Consolidated setup, development, and baseline testing.",
                    "duration_weeks": 2.0,
                    "priority": "HIGH",
                    "milestones": ["Discovery Complete", "MVP Completed"]
                },
                {
                    "title": "Deployment & Handoff",
                    "description": "Production rollout and operational training.",
                    "duration_weeks": 1.0,
                    "priority": "MEDIUM",
                    "milestones": ["Production Deployment", "Project Closure"]
                }
            ]
        else:
            return [
                {
                    "title": "Inception & Alignment",
                    "description": "Establish baseline requirements and technical design.",
                    "duration_weeks": 2.0,
                    "priority": "HIGH",
                    "milestones": ["Discovery Complete", "Architecture Approved"]
                },
                {
                    "title": "Alpha Implementation",
                    "description": "Core backend logic and initial API configurations.",
                    "duration_weeks": 4.0,
                    "priority": "MEDIUM",
                    "milestones": ["Alpha Integration Approved"]
                },
                {
                    "title": "Beta Validation",
                    "description": "User acceptance testing, security audits, and bug mitigation.",
                    "duration_weeks": 4.0,
                    "priority": "MEDIUM",
                    "milestones": ["User Acceptance Complete"]
                },
                {
                    "title": "Final Launch & Closure",
                    "description": "Production deployment and formal project closure.",
                    "duration_weeks": 2.0,
                    "priority": "HIGH",
                    "milestones": ["Production Deployment", "Project Closure"]
                }
            ]

    def generate_work_streams(self, project_details: dict[str, Any]) -> list[dict[str, Any]]:
        streams = [
            {
                "title": "Technology Work Stream",
                "description": "Focuses on infrastructure setup and microservices integrations.",
                "required_capabilities": self.recommend_capabilities("Technology Work Stream")
            },
            {
                "title": "Operations Work Stream",
                "description": "Focuses on process blueprint alignments.",
                "required_capabilities": self.recommend_capabilities("Operations Work Stream")
            }
        ]
        
        # Include compliance stream for higher complexity projects
        complexity = project_details.get("complexity", "Medium").lower()
        if complexity in ["high", "very high", "enterprise"]:
            streams.append({
                "title": "Compliance Work Stream",
                "description": "Handles security review constraints.",
                "required_capabilities": self.recommend_capabilities("Compliance Work Stream")
            })
            
        return streams

    def generate_milestones(self, project_details: dict[str, Any]) -> list[str]:
        phases = self.generate_phases(project_details)
        milestones = []
        for phase in phases:
            milestones.extend(phase.get("milestones", []))
        return list(set(milestones))

    def identify_dependencies(self, project_details: dict[str, Any]) -> list[dict[str, Any]]:
        phases = self.generate_phases(project_details)
        dependencies = []
        
        for i in range(1, len(phases)):
            dependencies.append({
                "task": phases[i]["title"],
                "depends_on": phases[i - 1]["title"],
                "type": "Finish-to-Start"
            })
            
        return dependencies

    def generate_delivery_plan(self, project_id: str, project_details: dict[str, Any]) -> DeliveryPlan:
        if not project_id:
            raise ValueError("Project ID is required.")
        if project_details is None:
            raise ValueError("Project details are required.")

        delivery_plan_id = self._generate_delivery_plan_id()
        
        LOGGER.info(
            "object_id=%s action=generate_delivery_plan actor=system status=DRAFT project_id=%s",
            delivery_plan_id,
            project_id,
        )

        phases = self.generate_phases(project_details)
        work_streams = self.generate_work_streams(project_details)
        dependencies = self.identify_dependencies(project_details)

        plan = DeliveryPlan(
            delivery_plan_id=delivery_plan_id,
            project_id=project_id,
            phases=phases,
            work_streams=work_streams,
            dependencies=dependencies,
        )

        LOGGER.info(
            "object_id=%s action=generate_delivery_plan actor=system status=READY project_id=%s",
            delivery_plan_id,
            project_id,
        )
        return plan
