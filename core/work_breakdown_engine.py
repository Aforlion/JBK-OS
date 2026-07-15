from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.delivery_plan import DeliveryPlan
from core.work_breakdown_structure import WorkBreakdownStructure

LOGGER = logging.getLogger(__name__)


class WorkBreakdownEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_wbs_id(self) -> str:
        wbs_id = f"WBS-{self._next_id:04d}"
        self._next_id += 1
        return wbs_id

    def calculate_task_effort(self, phase: dict[str, Any], stream: dict[str, Any]) -> float:
        duration_weeks = float(phase.get("duration_weeks", 2.0))
        # Baseline effort: 20 hours per week of duration
        effort = duration_weeks * 20.0
        
        # Scale based on stream type
        stream_title = stream.get("title", "").lower()
        if "tech" in stream_title or "technology" in stream_title:
            effort += 10.0  # Technical integration buffer
        elif "compliance" in stream_title or "security" in stream_title:
            effort -= 5.0   # Auditing/compliance tasks take less baseline hours
            
        return max(5.0, round(effort, 2))

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

    def generate_tasks(self, delivery_plan: DeliveryPlan) -> list[dict[str, Any]]:
        tasks = []
        phases = getattr(delivery_plan, "phases", [])
        streams = getattr(delivery_plan, "work_streams", [])
        
        # Keep track of generated task IDs by phase index
        tasks_by_phase: dict[int, list[str]] = {}

        for p_idx, phase in enumerate(phases):
            tasks_by_phase[p_idx] = []
            phase_title = phase.get("title", "Phase")
            priority = phase.get("priority", "MEDIUM")

            for s_idx, stream in enumerate(streams):
                stream_title = stream.get("title", "Work Stream")
                task_id = f"TSK-{p_idx + 1:02d}-{s_idx + 1:02d}"
                
                title = f"{phase_title} - {stream_title}"
                description = f"Execute deliverables for {stream_title} within the {phase_title} phase."
                
                # Recommend capabilities matching this specific task
                capabilities = self.recommend_capabilities(stream_title)
                effort = self.calculate_task_effort(phase, stream)
                
                # Advisory dependencies: tasks depend on all tasks in the prior phase
                dependencies = []
                if p_idx > 0:
                    dependencies = list(tasks_by_phase[p_idx - 1])

                task = {
                    "task_id": task_id,
                    "phase_title": phase_title,
                    "work_stream_title": stream_title,
                    "title": title,
                    "description": description,
                    "recommended_capabilities": capabilities,
                    "priority": priority,
                    "estimated_effort_hours": effort,
                    "dependencies": dependencies
                }
                tasks.append(task)
                tasks_by_phase[p_idx].append(task_id)

        return tasks

    def generate_wbs(self, delivery_plan: DeliveryPlan) -> WorkBreakdownStructure:
        if delivery_plan is None:
            raise ValueError("Delivery plan is required.")

        project_id = getattr(delivery_plan, "project_id", "UNKNOWN")
        delivery_plan_id = getattr(delivery_plan, "delivery_plan_id", "UNKNOWN")
        wbs_id = self._generate_wbs_id()

        LOGGER.info(
            "object_id=%s action=generate_wbs actor=system status=DRAFT project_id=%s",
            wbs_id,
            project_id,
        )

        tasks = self.generate_tasks(delivery_plan)

        wbs = WorkBreakdownStructure(
            wbs_id=wbs_id,
            project_id=project_id,
            delivery_plan_id=delivery_plan_id,
            tasks=tasks,
        )

        LOGGER.info(
            "object_id=%s action=generate_wbs actor=system status=READY project_id=%s",
            wbs_id,
            project_id,
        )
        return wbs
