from __future__ import annotations

from typing import Any

from core.deliverable import DeliverableStatus
from core.project import Project, ProjectStatus
from core.work_order import WorkOrder, WorkOrderPriority, WorkOrderStatus


class ChiefOfStaff:
    def __init__(
        self,
        worker_registry: Any,
        project_registry: Any,
        knowledge_registry: Any = None,
    ) -> None:
        if worker_registry is None:
            raise ValueError("Worker Registry is required.")
        if project_registry is None:
            raise ValueError("Project Registry is required.")

        self.worker_registry = worker_registry
        self.project_registry = project_registry
        self.knowledge_registry = knowledge_registry

    def create_project(
        self,
        title: str,
        client: str,
        description: str,
        project_id: str | None = None,
        status: ProjectStatus | str = ProjectStatus.PLANNED,
    ) -> Project:
        return Project(
            title=title,
            client=client,
            description=description,
            project_id=project_id,
            status=status,
        )

    def register_project(self, project: Project) -> Project:
        return self.project_registry.register(project)

    def create_work_order(
        self,
        project_id: str,
        title: str,
        objective: str,
        work_order_id: str | None = None,
        priority: WorkOrderPriority | str = WorkOrderPriority.MEDIUM,
    ) -> WorkOrder:
        project = self._require_project(project_id)
        work_order = WorkOrder(
            project_id=project.id,
            title=title,
            objective=objective,
            work_order_id=work_order_id,
            priority=priority,
        )
        project.add_work_order(work_order, actor="chief_of_staff")
        return work_order

    def assign_work_order(
        self,
        work_order_id: str,
        worker_id: str,
        assigned_by: str = "chief_of_staff",
    ) -> WorkOrder:
        work_order = self._require_work_order(work_order_id)
        self._require_mutable_work_order(work_order)
        worker = self._require_worker(worker_id)

        work_order.assign(
            assigned_by=assigned_by,
            assigned_to=worker.id,
            actor="chief_of_staff",
        )
        worker.receive_work_order(work_order, actor="chief_of_staff")
        return work_order

    def monitor_project(self, project_id: str) -> dict[str, Any]:
        project = self._require_project(project_id)
        return {
            "project": project.summary(),
            "work_orders": [
                work_order.summary()
                for work_order in project.work_orders
                if hasattr(work_order, "summary")
            ],
            "deliverables": [
                deliverable.summary()
                for deliverable in project.deliverables
                if hasattr(deliverable, "summary")
            ],
        }

    def collect_deliverable(self, deliverable: Any) -> Any:
        if deliverable is None:
            raise ValueError("Deliverable is required.")

        project = self._require_project(deliverable.project_id)
        work_order = self._require_work_order(deliverable.work_order_id)
        self._require_mutable_work_order(work_order)

        if work_order.project_id != project.id:
            raise ValueError("Deliverable project does not match WorkOrder project.")

        project.add_deliverable(deliverable, actor="chief_of_staff")
        work_order.attach_deliverable(deliverable.id, actor="chief_of_staff")
        return deliverable

    def complete_work_order(self, work_order_id: str, deliverable_id: str) -> WorkOrder:
        work_order = self._require_work_order(work_order_id)
        self._require_mutable_work_order(work_order)
        deliverable = self._require_deliverable(work_order.project_id, deliverable_id)

        if deliverable.work_order_id != work_order.id:
            raise ValueError("Deliverable does not belong to this WorkOrder.")
        if self._status_value(deliverable.status) != DeliverableStatus.APPROVED.value:
            raise ValueError("WorkOrder cannot complete without an APPROVED Deliverable.")

        if work_order.deliverable_id != deliverable.id:
            work_order.attach_deliverable(deliverable.id, actor="chief_of_staff")

        work_order.complete(actor="chief_of_staff")
        worker = self.worker_registry.find_by_id(work_order.assigned_to)
        if worker is not None and work_order in getattr(worker, "assigned_work_orders", []):
            worker.complete_work_order(work_order, actor="chief_of_staff")
        return work_order

    def generate_executive_brief(self) -> dict[str, Any]:
        projects = self.project_registry.list_projects()
        workers = self.worker_registry.list_workers()
        available_workers = self.worker_registry.list_available()

        completed_work_orders = []
        pending_work_orders = []
        completed_deliverables = []
        ceo_attention = []

        for project in projects:
            for work_order in project.work_orders:
                status = self._status_value(work_order.status)
                if status == WorkOrderStatus.COMPLETED.value:
                    completed_work_orders.append(work_order.summary())
                elif status != WorkOrderStatus.CANCELLED.value:
                    pending_work_orders.append(work_order.summary())

                priority = self._status_value(work_order.priority)
                if priority in {"HIGH", "CRITICAL"} and status != WorkOrderStatus.COMPLETED.value:
                    ceo_attention.append(work_order.summary())

            for deliverable in project.deliverables:
                if self._status_value(deliverable.status) == DeliverableStatus.APPROVED.value:
                    completed_deliverables.append(deliverable.summary())

        return {
            "projects_in_progress": [
                project.summary()
                for project in projects
                if self._status_value(project.status) == ProjectStatus.ACTIVE.value
            ],
            "completed_work_orders": completed_work_orders,
            "pending_work_orders": pending_work_orders,
            "available_workers": [
                worker.to_dict() if hasattr(worker, "to_dict") else worker
                for worker in available_workers
            ],
            "busy_workers": [
                worker.to_dict() if hasattr(worker, "to_dict") else worker
                for worker in workers
                if self._status_value(getattr(worker, "status", None)) == "BUSY"
            ],
            "completed_deliverables": completed_deliverables,
            "items_requiring_ceo_attention": ceo_attention,
        }

    def register_knowledge(self, knowledge_asset: Any) -> Any:
        """Validate and store a knowledge asset into the Knowledge Registry."""
        if knowledge_asset is None:
            raise ValueError("Knowledge asset is required.")
        if self.knowledge_registry is None:
            raise ValueError("No Knowledge Registry is configured on this Chief of Staff.")
        return self.knowledge_registry.register(knowledge_asset)

    def project_summary(self, project_id: str) -> dict[str, Any]:
        return self._require_project(project_id).summary()

    def _require_project(self, project_id: str) -> Project:
        project = self.project_registry.find_by_id(project_id)
        if project is None:
            raise ValueError(f"Project not found: {project_id}.")
        return project

    def _require_worker(self, worker_id: str) -> Any:
        worker = self.worker_registry.find_by_id(worker_id)
        if worker is None:
            raise ValueError(f"Worker not found: {worker_id}.")
        return worker

    def _require_work_order(self, work_order_id: str) -> WorkOrder:
        for project in self.project_registry.list_projects():
            for work_order in project.work_orders:
                if getattr(work_order, "id", None) == work_order_id:
                    return work_order
        raise ValueError(f"WorkOrder not found: {work_order_id}.")

    def _require_deliverable(self, project_id: str, deliverable_id: str) -> Any:
        project = self._require_project(project_id)
        for deliverable in project.deliverables:
            if getattr(deliverable, "id", None) == deliverable_id:
                return deliverable
        raise ValueError(f"Deliverable not found: {deliverable_id}.")

    @staticmethod
    def _require_mutable_work_order(work_order: WorkOrder) -> None:
        if ChiefOfStaff._status_value(work_order.status) in {
            WorkOrderStatus.COMPLETED.value,
            WorkOrderStatus.CANCELLED.value,
        }:
            raise ValueError("Completed and cancelled WorkOrders are read-only.")

    @staticmethod
    def _status_value(status: Any) -> Any:
        return getattr(status, "value", status)
