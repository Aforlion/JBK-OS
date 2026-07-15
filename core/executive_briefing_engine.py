from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

LOGGER = logging.getLogger(__name__)


class ExecutiveBriefingEngine:
    def __init__(
        self,
        chief_of_staff: Any,
        client_requests: list[Any] | None = None,
        workflows: list[Any] | None = None,
    ) -> None:
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")
        self.chief_of_staff = chief_of_staff
        self.client_requests = client_requests or []
        self.workflows = workflows or []

    def _get_workers(self) -> list[Any]:
        return self.chief_of_staff.worker_registry.list_workers()

    def _get_projects(self) -> list[Any]:
        return self.chief_of_staff.project_registry.list_projects()

    def _get_work_orders(self) -> list[Any]:
        work_orders = []
        for project in self._get_projects():
            work_orders.extend(project.work_orders)
        return work_orders

    def _get_deliverables(self) -> list[Any]:
        deliverables = []
        for project in self._get_projects():
            deliverables.extend(project.deliverables)
        return deliverables

    def generate_daily_briefing(self) -> dict[str, Any]:
        workers = self._get_workers()
        projects = self._get_projects()
        work_orders = self._get_work_orders()
        deliverables = self._get_deliverables()

        # Availability breakdown
        avail_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "AVAILABLE")
        busy_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "BUSY")
        offline_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "OFFLINE")
        suspended_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "SUSPENDED")

        # Project categorization
        active_projs = [p.summary() for p in projects if getattr(p.status, "value", p.status) == "ACTIVE"]
        completed_projs = [p.summary() for p in projects if getattr(p.status, "value", p.status) == "COMPLETED"]

        # WorkOrder categorization
        open_wos = [
            wo.summary()
            for wo in work_orders
            if getattr(wo.status, "value", wo.status) not in {"COMPLETED", "CANCELLED"}
        ]
        completed_wos = [
            wo.summary()
            for wo in work_orders
            if getattr(wo.status, "value", wo.status) == "COMPLETED"
        ]

        # Deliverable categorization
        pending_dels = [
            d.summary()
            for d in deliverables
            if getattr(d.status, "value", d.status) in {"DRAFT", "IN_REVIEW"}
        ]
        approved_dels = [
            d.summary()
            for d in deliverables
            if getattr(d.status, "value", d.status) == "APPROVED"
        ]

        # Client Requests
        new_reqs = [
            req.summary()
            for req in self.client_requests
            if getattr(req.status, "value", req.status) == "NEW"
        ]

        # Workflow Statuses
        wf_statuses = [
            {
                "state": getattr(wf, "state", "UNKNOWN"),
                "client_request_id": getattr(getattr(wf, "client_request", None), "id", None),
                "project_id": getattr(getattr(wf, "project", None), "id", None),
            }
            for wf in self.workflows
        ]

        attention_items = self.generate_ceo_attention_items()
        health = self._derive_operational_health(
            workers, projects, work_orders, deliverables, attention_items
        )

        return {
            "date": datetime.now(timezone.utc).isoformat(),
            "executive_availability": {
                "AVAILABLE": avail_count,
                "BUSY": busy_count,
                "OFFLINE": offline_count,
                "SUSPENDED": suspended_count,
            },
            "active_projects": active_projs,
            "completed_projects": completed_projs,
            "open_work_orders": open_wos,
            "completed_work_orders": completed_wos,
            "pending_deliverables": pending_dels,
            "approved_deliverables": approved_dels,
            "new_client_requests": new_reqs,
            "workflow_status": wf_statuses,
            "items_requiring_ceo_attention": attention_items,
            "operational_health": health,
        }

    def generate_project_summary(self) -> list[dict[str, Any]]:
        return [project.summary() for project in self._get_projects()]

    def generate_workload_summary(self) -> dict[str, Any]:
        workers = self._get_workers()
        workload = {}
        for worker in workers:
            workload[worker.id] = {
                "title": worker.title,
                "status": getattr(worker.status, "value", worker.status),
                "assigned_work_orders": [
                    wo.summary() for wo in getattr(worker, "assigned_work_orders", [])
                ],
                "completed_work_orders": [
                    wo.summary() for wo in getattr(worker, "completed_work_orders", [])
                ],
            }
        return workload

    def generate_risk_summary(self) -> dict[str, Any]:
        attention_items = self.generate_ceo_attention_items()
        
        # Categorize risks
        suspended_execs = [item for item in attention_items if item["type"] == "SUSPENDED_EXECUTIVE"]
        workflow_failures = [item for item in attention_items if item["type"] == "WORKFLOW_FAILURE"]
        unassigned_wos = [item for item in attention_items if item["type"] == "UNASSIGNED_WORK_ORDER"]
        rejected_dels = [item for item in attention_items if item["type"] == "REJECTED_DELIVERABLE"]
        critical_requests = [item for item in attention_items if item["type"] == "CRITICAL_CLIENT_REQUEST"]
        projects_no_work = [item for item in attention_items if item["type"] == "PROJECT_WITHOUT_ASSIGNED_WORK"]

        return {
            "total_risks_identified": len(attention_items),
            "suspended_executives_count": len(suspended_execs),
            "workflow_failures_count": len(workflow_failures),
            "unassigned_work_orders_count": len(unassigned_wos),
            "rejected_deliverables_count": len(rejected_dels),
            "critical_client_requests_count": len(critical_requests),
            "projects_without_assigned_work_count": len(projects_no_work),
            "risks": attention_items,
        }

    def generate_ceo_attention_items(self) -> list[dict[str, Any]]:
        attention_items = []

        # 1. Projects without assigned work (active projects with no work orders)
        for project in self._get_projects():
            if getattr(project.status, "value", project.status) == "ACTIVE":
                if not project.work_orders:
                    attention_items.append(
                        {
                            "type": "PROJECT_WITHOUT_ASSIGNED_WORK",
                            "id": project.id,
                            "title": project.title,
                            "description": "Active project has no associated work orders.",
                        }
                    )

        # 2. Rejected Deliverables
        for deliverable in self._get_deliverables():
            if getattr(deliverable.status, "value", deliverable.status) == "REJECTED":
                attention_items.append(
                    {
                        "type": "REJECTED_DELIVERABLE",
                        "id": deliverable.id,
                        "title": deliverable.title,
                        "project_id": deliverable.project_id,
                        "work_order_id": deliverable.work_order_id,
                        "description": "Deliverable has been rejected.",
                    }
                )

        # 3. Critical priority Client Requests
        for req in self.client_requests:
            priority = getattr(req.priority, "value", req.priority)
            if priority == "CRITICAL" and getattr(req.status, "value", req.status) not in {"APPROVED", "PROJECT_CREATED", "REJECTED", "WITHDRAWN"}:
                attention_items.append(
                    {
                        "type": "CRITICAL_CLIENT_REQUEST",
                        "id": req.id,
                        "title": req.title,
                        "client_name": req.client_name,
                        "description": "Client request is marked critical priority.",
                    }
                )

        # 4. Workflow failures
        for wf in self.workflows:
            state = getattr(wf, "state", None)
            if state == "FAILED":
                req_id = getattr(getattr(wf, "client_request", None), "id", None)
                attention_items.append(
                    {
                        "type": "WORKFLOW_FAILURE",
                        "state": state,
                        "client_request_id": req_id,
                        "description": "Orchestrator workflow has failed.",
                    }
                )

        # 5. Executives marked SUSPENDED
        for worker in self._get_workers():
            if getattr(worker.status, "value", worker.status) == "SUSPENDED":
                attention_items.append(
                    {
                        "type": "SUSPENDED_EXECUTIVE",
                        "id": worker.id,
                        "title": worker.title,
                        "description": "Executive staff status is marked suspended.",
                    }
                )

        # 6. Unassigned WorkOrders
        for wo in self._get_work_orders():
            status = getattr(wo.status, "value", wo.status)
            if status == "CREATED" or not wo.assigned_to:
                if status not in {"COMPLETED", "CANCELLED"}:
                    attention_items.append(
                        {
                            "type": "UNASSIGNED_WORK_ORDER",
                            "id": wo.id,
                            "title": wo.title,
                            "project_id": wo.project_id,
                            "description": "Work order is not assigned to any executive.",
                        }
                    )

        return attention_items

    def generate_summary(self) -> dict[str, Any]:
        workers = self._get_workers()
        projects = self._get_projects()
        work_orders = self._get_work_orders()
        deliverables = self._get_deliverables()
        attention_items = self.generate_ceo_attention_items()

        avail_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "AVAILABLE")
        busy_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "BUSY")
        health = self._derive_operational_health(
            workers, projects, work_orders, deliverables, attention_items
        )

        return {
            "total_executives": len(workers),
            "available_executives": avail_count,
            "busy_executives": busy_count,
            "projects": len(projects),
            "work_orders": len(work_orders),
            "deliverables": len(deliverables),
            "client_requests": len(self.client_requests),
            "operational_health": health,
            "ceo_attention_count": len(attention_items),
        }

    def _derive_operational_health(
        self,
        workers: list[Any],
        projects: list[Any],
        work_orders: list[Any],
        deliverables: list[Any],
        attention_items: list[dict[str, Any]],
    ) -> str:
        # Check active projects count first
        active_projects_count = sum(
            1 for p in projects if getattr(p.status, "value", p.status) == "ACTIVE"
        )
        
        # Rule: No active projects -> HEALTHY
        if active_projects_count == 0:
            return "HEALTHY"

        # Rule: No available executives -> WARNING
        avail_count = sum(1 for w in workers if getattr(w.status, "value", w.status) == "AVAILABLE")
        if len(workers) > 0 and avail_count == 0:
            return "WARNING"

        # Rule: Rejected workflow -> WARNING
        failed_workflows = sum(1 for wf in self.workflows if getattr(wf, "state", None) == "FAILED")
        if failed_workflows > 0:
            return "WARNING"

        # Rule: Multiple blocked projects -> WARNING
        # Let's count projects with unassigned work orders or no work orders
        blocked_projs = 0
        for project in projects:
            if getattr(project.status, "value", project.status) == "ACTIVE":
                if not project.work_orders:
                    blocked_projs += 1
                elif any(
                    getattr(wo.status, "value", wo.status) == "CREATED" or not wo.assigned_to
                    for wo in project.work_orders
                ):
                    blocked_projs += 1
        if blocked_projs >= 2:
            return "WARNING"

        # If there's a highly critical state: both no available workers and failed workflows
        if failed_workflows > 0 and avail_count == 0:
            return "CRITICAL"

        return "HEALTHY"
