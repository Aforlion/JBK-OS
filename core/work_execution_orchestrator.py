from __future__ import annotations

import logging
import traceback
from typing import Any
from datetime import datetime, timezone

from core.project import Project
from core.work_order import WorkOrder, WorkOrderStatus
from core.skill_registry import SkillRegistry
from core.chief_of_staff import ChiefOfStaff
from core.deliverable import Deliverable, DeliverableStatus
from core.execution_report import ExecutionReport

LOGGER = logging.getLogger(__name__)


class WorkExecutionOrchestrator:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_report_id(self) -> str:
        rep_id = f"EXP-{self._next_id:04d}"
        self._next_id += 1
        return rep_id

    def execute_work_order(
        self,
        work_order: WorkOrder,
        project: Project,
        skill_registry: SkillRegistry,
        execution_planner: Any,
        chief_of_staff: ChiefOfStaff,
    ) -> ExecutionReport:
        if work_order is None:
            raise ValueError("Work order is required.")
        if project is None:
            raise ValueError("Project is required.")
        if skill_registry is None:
            raise ValueError("Skill registry is required.")
        if execution_planner is None:
            raise ValueError("Execution planner is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        report_id = self._generate_report_id()
        worker_id = work_order.assigned_to or "chief_of_staff"

        # 1. Dependency Satisfaction Check
        dependencies = getattr(work_order, "dependencies", [])
        for dep_id in dependencies:
            # Find the dependent work order in the project
            dep_wo = None
            for wo in project.work_orders:
                if wo.id == dep_id or getattr(wo, "task_id", None) == dep_id:
                    dep_wo = wo
                    break
            
            if dep_wo:
                status_val = getattr(dep_wo.status, "value", dep_wo.status)
                if status_val != WorkOrderStatus.COMPLETED and status_val != "COMPLETED":
                    # Dependency is not complete. Status must wait.
                    work_order.status = "WAITING"
                    
                    LOGGER.warning(
                        "object_id=%s action=execute_work_order actor=system status=WAITING work_order_id=%s reason=blocked_dependency",
                        report_id,
                        work_order.id,
                    )
                    return ExecutionReport(
                        report_id=report_id,
                        work_order_id=work_order.id,
                        engine_name="None",
                        worker_id=worker_id,
                        status="WAITING",
                        duration_seconds=0.0,
                        outputs={"logs": f"Execution blocked. Dependency {dep_id} is in status {status_val}."},
                        errors=[f"Dependency {dep_id} is not complete."],
                    )

        # 2. Consult Execution Planner
        try:
            recommendation = execution_planner.get_recommendation(work_order)
            skill_id = recommendation.get("skill_id")
            engine_name = recommendation.get("engine_name", "Antigravity")
        except Exception as e:
            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name="Unknown",
                worker_id=worker_id,
                status="FAILED",
                duration_seconds=0.0,
                outputs={"logs": "Execution planner consultation failed."},
                errors=[f"Execution planner error: {str(e)}"],
            )

        # 3. Look up Skill in Registry
        skill = skill_registry.find_by_id(skill_id)
        if not skill:
            work_order.status = WorkOrderStatus.CANCELLED
            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name=engine_name,
                worker_id=worker_id,
                status="FAILED",
                duration_seconds=0.0,
                outputs={"logs": f"Skill lookup failed for ID: {skill_id}."},
                errors=[f"Skill {skill_id} not found in registry."],
            )

        skill_status = getattr(skill.status, "value", skill.status)
        if skill_status != "AVAILABLE" and skill_status != "AVAILABLE":
            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name=engine_name,
                worker_id=worker_id,
                status="FAILED",
                duration_seconds=0.0,
                outputs={"logs": f"Skill {skill_id} is unavailable (status: {skill_status})."},
                errors=[f"Skill {skill_id} is not available."],
            )

        # Verify Execution Engine supports the Skill (advisory check)
        if not getattr(skill, "execution_engine", None):
            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name=engine_name,
                worker_id=worker_id,
                status="FAILED",
                duration_seconds=0.0,
                outputs={"logs": f"Engine {engine_name} does not support Skill {skill_id} due to missing engine specs."},
                errors=[f"Skill {skill_id} does not configure execution_engine."],
            )

        # 4. Dispatch and Monitor Execution
        LOGGER.info(
            "object_id=%s action=execute_work_order actor=system status=QUEUED work_order_id=%s",
            report_id,
            work_order.id,
        )

        # Transition work order through accepted/in progress
        try:
            if work_order.assigned_to:
                # Accept and start
                work_order.accept(actor="system")
                work_order.start(actor="system")
            
            # Simulate execution time and capture logs
            duration = 1.5
            stdout = f"Executing work order {work_order.id} using skill {skill.name} on engine {engine_name}.\nSuccess."
            
            # 5. Create Deliverables
            deliverable = Deliverable(
                project_id=project.id,
                work_order_id=work_order.id,
                title=f"Deliverable for {work_order.title}",
                author=worker_id,
                content={"stdout": stdout, "logs": "Completed successfully."},
            )
            
            # Submit and approve deliverable
            deliverable.submit_for_review(actor="system")
            deliverable.approve(actor="system")

            # Attach deliverable to WorkOrder
            work_order.attach_deliverable(deliverable.id, actor="system")
            
            # Complete the work order
            work_order.complete(actor="system")

            # Notify Chief of Staff / update worker if registered
            if work_order.assigned_to:
                worker = chief_of_staff.worker_registry.find_by_id(work_order.assigned_to)
                if worker and hasattr(worker, "complete_work_order"):
                    try:
                        worker.complete_work_order(work_order, actor="system")
                    except Exception:
                        pass # Ignore if already updated

            LOGGER.info(
                "object_id=%s action=execute_work_order actor=system status=COMPLETED work_order_id=%s",
                report_id,
                work_order.id,
            )

            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name=engine_name,
                worker_id=worker_id,
                status="COMPLETED",
                duration_seconds=duration,
                outputs={
                    "stdout": stdout,
                    "deliverable_id": deliverable.id,
                },
                errors=[],
            )

        except Exception as e:
            tb = traceback.format_exc()
            work_order.status = WorkOrderStatus.CANCELLED
            LOGGER.error("Execution failed: %s\n%s", str(e), tb)
            return ExecutionReport(
                report_id=report_id,
                work_order_id=work_order.id,
                engine_name=engine_name,
                worker_id=worker_id,
                status="FAILED",
                duration_seconds=0.1,
                outputs={"logs": "Execution crashed."},
                errors=[f"Runtime error: {str(e)}"],
            )
