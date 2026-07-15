from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.project import Project
from core.resource_allocation_plan import ResourceAllocationPlan
from core.chief_of_staff import ChiefOfStaff
from core.work_order import WorkOrder
from core.work_order_generation_report import WorkOrderGenerationReport

LOGGER = logging.getLogger(__name__)


class WorkOrderGenerationEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_generation_id(self) -> str:
        gen_id = f"WOG-{self._next_id:04d}"
        self._next_id += 1
        return gen_id

    def generate_work_orders(
        self,
        project: Project,
        resource_allocation_plan: ResourceAllocationPlan,
        chief_of_staff: ChiefOfStaff,
    ) -> WorkOrderGenerationReport:
        if project is None:
            raise ValueError("Project is required.")
        if resource_allocation_plan is None:
            raise ValueError("Resource allocation plan is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        if resource_allocation_plan.project_id != project.id:
            raise ValueError(
                f"Project ID mismatch: plan has {resource_allocation_plan.project_id}, "
                f"project is {project.id}."
            )

        generation_id = self._generate_generation_id()
        LOGGER.info(
            "object_id=%s action=generate_work_orders actor=system status=DRAFT project_id=%s",
            generation_id,
            project.id,
        )

        created_wo_instances: list[WorkOrder] = []
        created_work_orders_summary = []
        warnings = []

        # 1. Verification of workers before creation to ensure atomicity
        for assignment in resource_allocation_plan.assignments:
            worker_id = assignment.get("worker_id")
            if not worker_id:
                raise ValueError(f"Missing worker assignment for task {assignment.get('task_id')}.")
            worker = chief_of_staff.worker_registry.find_by_id(worker_id)
            if not worker:
                raise ValueError(f"Worker {worker_id} is not registered.")
            
            # Check availability
            status = getattr(worker, "status", None)
            status_val = getattr(status, "value", status)
            if status_val != "AVAILABLE":
                raise ValueError(f"Worker {worker_id} is not available (status: {status_val}).")

        # 2. Main generation loop with rollback transaction block
        try:
            for assignment in resource_allocation_plan.assignments:
                task_id = assignment.get("task_id")
                worker_id = assignment.get("worker_id")
                title = assignment.get("title", f"Work Order for {task_id}")
                objective = assignment.get("description", "Execute assigned task deliverables.")
                priority = assignment.get("priority", "MEDIUM")
                estimated_load = assignment.get("estimated_load", 0.0)
                capability_match = assignment.get("capability_match", [])
                dependencies = assignment.get("dependencies", [])

                # Create work order
                work_order = chief_of_staff.create_work_order(
                    project_id=project.id,
                    title=title,
                    objective=objective,
                    priority=priority,
                )
                created_wo_instances.append(work_order)

                # Assign work order
                chief_of_staff.assign_work_order(work_order.id, worker_id)

                # Set dynamic properties for traceability and scheduling
                setattr(work_order, "estimated_hours", estimated_load)
                setattr(work_order, "required_capabilities", capability_match)
                setattr(work_order, "dependencies", dependencies)
                setattr(work_order, "task_id", task_id)

                created_work_orders_summary.append({
                    "work_order_id": work_order.id,
                    "task_id": task_id,
                    "title": title,
                    "assigned_to": worker_id,
                    "priority": str(priority),
                    "status": getattr(work_order.status, "value", work_order.status),
                })
        except Exception as e:
            LOGGER.error("Failed to generate work orders. Rolling back. Error: %s", str(e))
            # Rollback: remove created work orders from project and cleanup assignment lists
            for wo in created_wo_instances:
                # Remove from project work orders
                if wo in project.work_orders:
                    project.work_orders.remove(wo)
                # Note: unregister from registry if registered. But chief_of_staff doesn't expose a delete,
                # we can directly clear worker assignment if set
                if wo.assigned_to:
                    worker = chief_of_staff.worker_registry.find_by_id(wo.assigned_to)
                    if worker and wo in getattr(worker, "assigned_work_orders", []):
                        worker.assigned_work_orders.remove(wo)
            raise ValueError(f"Work order generation failed, rolled back: {str(e)}") from e

        # Handle skipped / unassigned tasks
        skipped_tasks = []
        for task in resource_allocation_plan.unassigned_tasks:
            skipped_tasks.append({
                "task_id": task.get("task_id"),
                "title": task.get("title", "Unassigned Task"),
                "status": "PENDING_RESOURCE",
                "recommended_capabilities": task.get("recommended_capabilities", []),
            })
            warnings.append(f"Task {task.get('task_id')} skipped: status is PENDING_RESOURCE.")

        # Construct dependency graph mapping WBS task IDs
        dependency_graph = {}
        for assignment in resource_allocation_plan.assignments:
            dependency_graph[assignment["task_id"]] = assignment.get("dependencies", [])
        for task in resource_allocation_plan.unassigned_tasks:
            dependency_graph[task["task_id"]] = task.get("dependencies", [])

        # Calculate metrics
        total_tasks = len(resource_allocation_plan.assignments) + len(resource_allocation_plan.unassigned_tasks)
        generated_count = len(created_work_orders_summary)
        pending_resources = len(skipped_tasks)
        
        efforts = [float(assignment.get("estimated_load", 0.0)) for assignment in resource_allocation_plan.assignments]
        avg_effort = round(sum(efforts) / len(efforts), 2) if efforts else 0.0

        # Simple critical path count: tasks with no incoming dependencies (i.e. leaf nodes)
        dep_targets = set()
        for deps in dependency_graph.values():
            dep_targets.update(deps)
        critical_path_count = sum(1 for task_id in dependency_graph if task_id not in dep_targets)

        summary_metrics = {
            "total_tasks": total_tasks,
            "generated": generated_count,
            "pending_resources": pending_resources,
            "failed": 0,
            "average_effort": avg_effort,
            "critical_path_count": critical_path_count,
        }

        report = WorkOrderGenerationReport(
            generation_id=generation_id,
            project_id=project.id,
            created_work_orders=created_work_orders_summary,
            skipped_tasks=skipped_tasks,
            dependency_graph=dependency_graph,
            warnings=warnings,
            summary=summary_metrics,
        )

        LOGGER.info(
            "object_id=%s action=generate_work_orders actor=system status=READY project_id=%s",
            generation_id,
            project.id,
        )
        return report
