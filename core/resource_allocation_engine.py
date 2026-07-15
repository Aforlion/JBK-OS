from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.work_breakdown_structure import WorkBreakdownStructure
from core.worker_registry import WorkerRegistry
from core.skill_registry import SkillRegistry
from core.resource_allocation_plan import ResourceAllocationPlan

LOGGER = logging.getLogger(__name__)


class ResourceAllocationEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_allocation_id(self) -> str:
        all_id = f"ALL-{self._next_id:04d}"
        self._next_id += 1
        return all_id

    def allocate_resources(
        self,
        wbs: WorkBreakdownStructure,
        worker_registry: WorkerRegistry,
        skill_registry: SkillRegistry,
        execution_planner: Any = None,
    ) -> ResourceAllocationPlan:
        if wbs is None:
            raise ValueError("Work breakdown structure is required.")
        if worker_registry is None:
            raise ValueError("Worker registry is required.")
        if skill_registry is None:
            raise ValueError("Skill registry is required.")

        project_id = getattr(wbs, "project_id", "UNKNOWN")
        allocation_id = self._generate_allocation_id()

        LOGGER.info(
            "object_id=%s action=allocate_resources actor=system status=DRAFT project_id=%s",
            allocation_id,
            project_id,
        )

        assignments = []
        unassigned_tasks = []
        warnings = []
        
        # Track workload per worker ID
        workload_summary: dict[str, float] = {}
        tasks_count_per_worker: dict[str, int] = {}
        
        # Get available workers
        available_workers = worker_registry.list_available()
        available_departments = set()
        
        # Initialize workload tracking for available workers
        for worker in available_workers:
            workload_summary[worker.id] = 0.0
            tasks_count_per_worker[worker.id] = 0
            
            # Extract department from worker or default
            dept = getattr(worker, "department", None)
            if not dept:
                # Fallback to checking skills owned by this worker
                owned_skills = skill_registry.find_by_owner(worker.id)
                if owned_skills:
                    dept = owned_skills[0].department
            available_departments.add(dept or "Technology")

        # Process each WBS task
        for task in getattr(wbs, "tasks", []):
            task_id = task.get("task_id")
            required_caps = [c.strip().lower() for c in task.get("recommended_capabilities", [])]
            estimated_load = float(task.get("estimated_effort_hours", 0.0))
            
            if not required_caps:
                # If no capabilities required, assign to anyone or mark unassigned
                unassigned_tasks.append(task)
                warnings.append(f"Task {task_id} has no recommended capabilities.")
                continue

            candidates = []
            
            for worker in available_workers:
                # Resolve worker capabilities
                worker_caps = [c.strip().lower() for c in getattr(worker, "capabilities", [])]
                
                # Fetch skills owned by this worker
                owned_skills = skill_registry.find_by_owner(worker.id)
                for skill in owned_skills:
                    worker_caps.extend([c.strip().lower() for c in getattr(skill, "capabilities", [])])
                
                # Find overlap
                matched_caps = [c for c in required_caps if c in worker_caps]
                if matched_caps:
                    candidates.append({
                        "worker": worker,
                        "matched_caps": matched_caps,
                        "match_count": len(matched_caps)
                    })

            if candidates:
                # Rank candidates:
                # 1. match_count (highest first)
                # 2. current workload (lowest load hours first)
                # 3. worker title/ID (fallback)
                candidates.sort(key=lambda c: (
                    -c["match_count"],
                    workload_summary[c["worker"].id],
                    c["worker"].id
                ))
                
                best_match = candidates[0]
                best_worker = best_match["worker"]
                w_id = best_worker.id
                
                # Update workload tracking
                workload_summary[w_id] += estimated_load
                tasks_count_per_worker[w_id] += 1
                
                # Resolve worker name and department
                worker_name = getattr(best_worker, "title", "Worker")
                worker_dept = getattr(best_worker, "department", None)
                if not worker_dept:
                    owned_skills = skill_registry.find_by_owner(w_id)
                    worker_dept = owned_skills[0].department if owned_skills else "Technology"

                confidence = round(best_match["match_count"] / len(required_caps), 2)
                
                assignments.append({
                    "task_id": task_id,
                    "worker_id": w_id,
                    "worker_name": worker_name,
                    "department": worker_dept,
                    "confidence": confidence,
                    "capability_match": best_match["matched_caps"],
                    "estimated_load": estimated_load,
                    "rationale": f"Matched capabilities: {', '.join(best_match['matched_caps'])}.",
                    "title": task.get("title", "Task"),
                    "description": task.get("description", ""),
                    "priority": task.get("priority", "MEDIUM"),
                    "dependencies": task.get("dependencies", [])
                })
            else:
                unassigned_tasks.append(task)
                warnings.append(f"Task {task_id} is unassigned: no available worker matches capabilities.")

        # Overloaded worker warnings (> 40.0 hours)
        for w_id, load in workload_summary.items():
            if load > 40.0:
                warnings.append(f"Worker {w_id} is overloaded with {load} hours of estimated load.")

        # Utilization compilation
        utilization = {}
        for worker in available_workers:
            w_id = worker.id
            utilization[w_id] = {
                "task_count": tasks_count_per_worker[w_id],
                "total_hours": workload_summary[w_id],
                "status": "Busy" if workload_summary[w_id] > 0 else "Available"
            }

        plan = ResourceAllocationPlan(
            allocation_id=allocation_id,
            project_id=project_id,
            assignments=assignments,
            unassigned_tasks=unassigned_tasks,
            workload_summary=workload_summary,
            utilization=utilization,
            warnings=warnings,
        )

        LOGGER.info(
            "object_id=%s action=allocate_resources actor=system status=READY project_id=%s",
            allocation_id,
            project_id,
        )
        return plan
