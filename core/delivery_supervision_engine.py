from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.project import Project
from core.worker_registry import WorkerRegistry
from core.work_order import WorkOrder, WorkOrderStatus
from core.delivery_status_report import DeliveryStatusReport

LOGGER = logging.getLogger(__name__)


class DeliverySupervisionEngine:
    def __init__(self) -> None:
        self._next_id = 1

    def _generate_report_id(self) -> str:
        rep_id = f"SUP-{self._next_id:04d}"
        self._next_id += 1
        return rep_id

    def supervise_project(
        self,
        project: Project,
        worker_registry: WorkerRegistry,
    ) -> DeliveryStatusReport:
        if project is None:
            raise ValueError("Project is required.")
        if worker_registry is None:
            raise ValueError("Worker registry is required.")

        report_id = self._generate_report_id()
        LOGGER.info(
            "object_id=%s action=supervise_project actor=system status=DRAFT project_id=%s",
            report_id,
            project.id,
        )

        active_work = []
        waiting_work = []
        completed_work = []
        failed_work = []

        # 1. Classify active work orders
        for wo in project.work_orders:
            status_val = getattr(wo.status, "value", wo.status)
            wo_dict = {
                "work_order_id": wo.id,
                "title": wo.title,
                "assigned_to": wo.assigned_to,
                "status": status_val,
                "priority": str(wo.priority),
                "estimated_hours": getattr(wo, "estimated_hours", 0.0),
            }
            if status_val == "COMPLETED" or status_val == WorkOrderStatus.COMPLETED:
                completed_work.append(wo_dict)
            elif status_val == "FAILED" or status_val == "CANCELLED" or status_val == WorkOrderStatus.CANCELLED:
                failed_work.append(wo_dict)
            elif status_val == "WAITING" or status_val == "WAIT":
                waiting_work.append(wo_dict)
            else:
                active_work.append(wo_dict)

        # 2. Worker Utilization Calculations
        worker_utilization = {}
        for worker in worker_registry.list_workers():
            assigned_hours = 0.0
            completed_hours = 0.0
            remaining_hours = 0.0
            current_tasks = []

            for wo in project.work_orders:
                if wo.assigned_to == worker.id:
                    hours = float(getattr(wo, "estimated_hours", 0.0) or 0.0)
                    assigned_hours += hours
                    status_val = getattr(wo.status, "value", wo.status)
                    if status_val == "COMPLETED" or status_val == WorkOrderStatus.COMPLETED:
                        completed_hours += hours
                    else:
                        remaining_hours += hours
                        current_tasks.append(wo.id)

            utilization_pct = round((assigned_hours / 40.0) * 100.0, 2)
            
            worker_utilization[worker.id] = {
                "worker_id": worker.id,
                "worker_name": getattr(worker, "title", "Worker"),
                "assigned_hours": assigned_hours,
                "completed_hours": completed_hours,
                "remaining_hours": remaining_hours,
                "current_tasks": current_tasks,
                "utilization_pct": utilization_pct,
                "status": getattr(worker.status, "value", worker.status),
            }

        # 3. Blocker Detection
        blockers = []
        for wo in project.work_orders:
            status_val = getattr(wo.status, "value", wo.status)
            
            # Check WAITING state
            if status_val == "WAITING":
                blockers.append({
                    "work_order_id": wo.id,
                    "type": "WAIT_LOCK",
                    "description": f"Work order {wo.id} is waiting on dependency completion."
                })
            
            # Check missing worker assignment
            if status_val not in ["COMPLETED", "CANCELLED"] and not wo.assigned_to:
                blockers.append({
                    "work_order_id": wo.id,
                    "type": "MISSING_WORKER",
                    "description": f"Work order {wo.id} is not complete and has no assigned worker."
                })

        # 4. CEO Attention Rules & Escalations
        ceo_attention_items = []
        corrective_recommendations = []
        risk_register = []

        # Overloaded worker check
        for w_id, util in worker_utilization.items():
            if util["utilization_pct"] > 100.0:
                ceo_attention_items.append({
                    "type": "WORKER_OVERLOADED",
                    "target": w_id,
                    "description": f"Worker {w_id} has exceeded 100% capacity (utilization: {util['utilization_pct']}%)."
                })
                corrective_recommendations.append({
                    "action": "Reassign task",
                    "target": w_id,
                    "rationale": "Balance resource workload below 100% threshold."
                })
                risk_register.append({
                    "risk": f"Resource overload on {w_id}",
                    "severity": "HIGH"
                })

        # Blocked task check
        for b in blockers:
            # check if blocked task is High/Critical priority
            wo = next((w for w in project.work_orders if w.id == b["work_order_id"]), None)
            if wo:
                priority_str = str(wo.priority).upper()
                if "HIGH" in priority_str or "CRITICAL" in priority_str:
                    ceo_attention_items.append({
                        "type": "CRITICAL_PATH_BLOCKED",
                        "target": wo.id,
                        "description": f"Critical/High priority task {wo.id} is blocked: {b['description']}."
                    })
                    corrective_recommendations.append({
                        "action": "Escalate to CTO",
                        "target": wo.id,
                        "rationale": "Clear execution roadblock on critical path."
                    })
                    risk_register.append({
                        "risk": f"Blocker on critical path task {wo.id}",
                        "severity": "CRITICAL"
                    })

        # Failed execution check
        if failed_work:
            for fw in failed_work:
                ceo_attention_items.append({
                    "type": "EXECUTION_FAILURE",
                    "target": fw["work_order_id"],
                    "description": f"Work order {fw['work_order_id']} has failed."
                })
                corrective_recommendations.append({
                    "action": "Initiate recovery workflow",
                    "target": fw["work_order_id"],
                    "rationale": "Rerun failed dispatch task."
                })
                risk_register.append({
                    "risk": f"Failed execution of work order {fw['work_order_id']}",
                    "severity": "HIGH"
                })

        # 5. Project Health Determination
        health_status = "HEALTHY"
        if len(failed_work) > 0 or any(r["severity"] == "CRITICAL" for r in risk_register):
            health_status = "CRITICAL"
        elif len(blockers) > 1 or any(r["severity"] == "HIGH" for r in risk_register):
            health_status = "AT_RISK"
        elif len(blockers) == 1 or any(util["utilization_pct"] > 90.0 for util in worker_utilization.values()):
            health_status = "WATCH"

        report = DeliveryStatusReport(
            report_id=report_id,
            project_id=project.id,
            health_status=health_status,
            active_work=active_work,
            waiting_work=waiting_work,
            completed_work=completed_work,
            failed_work=failed_work,
            risk_register=risk_register,
            worker_utilization=worker_utilization,
            blockers=blockers,
            ceo_attention_items=ceo_attention_items,
            corrective_recommendations=corrective_recommendations,
        )

        LOGGER.info(
            "object_id=%s action=supervise_project actor=system status=READY project_id=%s",
            report_id,
            project.id,
        )
        return report
