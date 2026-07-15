from __future__ import annotations

from enum import Enum
import logging
from typing import Any
from datetime import datetime, timezone

from core.client_request import ClientRequest, ClientRequestStatus, ClientRequestPriority
from core.project import Project, ProjectStatus
from core.work_order import WorkOrder, WorkOrderPriority, WorkOrderStatus
from core.deliverable import DeliverableStatus

LOGGER = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BusinessProcessWorkflow:
    def __init__(self, chief_of_staff: Any) -> None:
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")
        self.chief_of_staff = chief_of_staff
        self.state = WorkflowState.NOT_STARTED
        self.client_request: ClientRequest | None = None
        self.project: Project | None = None
        self.work_orders: list[WorkOrder] = []
        self.deliverables: list[Any] = []
        self.assignments: dict[str, str] = {}  # work_order_id -> worker_id
        self._items_requiring_ceo_attention: list[dict[str, Any]] = []

    def start(self, client_request: ClientRequest) -> None:
        if client_request is None:
            raise ValueError("Client request is required.")
        
        self.client_request = client_request
        self.state = WorkflowState.RUNNING
        self._log_state_change("start", "system", "started")
        
        # Check if the request is already in a terminal state
        status = getattr(client_request.status, "value", client_request.status)
        if status == ClientRequestStatus.REJECTED.value:
            self.state = WorkflowState.FAILED
            self._log_state_change("start", "system", "failed_due_to_rejection")
            return
        elif status == ClientRequestStatus.WITHDRAWN.value:
            self.state = WorkflowState.CANCELLED
            self._log_state_change("start", "system", "cancelled_due_to_withdrawal")
            return

        # Perform request validation
        if not self.validate_request():
            status = getattr(self.client_request.status, "value", self.client_request.status)
            if status == ClientRequestStatus.REJECTED.value:
                self.state = WorkflowState.FAILED
            elif status == ClientRequestStatus.WITHDRAWN.value:
                self.state = WorkflowState.CANCELLED
            else:
                self.state = WorkflowState.FAILED
            self._log_state_change("start", "system", f"validation_failed_status_{status}")
            return

        self.process_request()

    def validate_request(self) -> bool:
        if self.client_request is None:
            return False
            
        status = getattr(self.client_request.status, "value", self.client_request.status)
        if status in {ClientRequestStatus.REJECTED.value, ClientRequestStatus.WITHDRAWN.value}:
            return False
        
        if status in {ClientRequestStatus.APPROVED.value, ClientRequestStatus.PROJECT_CREATED.value}:
            return True
            
        # Basic validation: ensure we have necessary fields to proceed
        if not self.client_request.client_name or not self.client_request.title:
            self.client_request.reject(actor="workflow")
            return False
            
        # Approve request if not already approved
        self.client_request.approve(actor="workflow")
        return True

    def process_request(self) -> None:
        if self.state != WorkflowState.RUNNING:
            return

        # Coordinate project creation
        self.create_project()
        
        # Coordinate work order creation and assignment
        self.assign_initial_work()
        
        # Monitor execution
        self.monitor_execution()

    def create_project(self) -> Project:
        if self.client_request is None:
            raise ValueError("Client request is missing.")
            
        # If project is already linked to client request, load it
        if self.client_request.project_id:
            self.project = self.chief_of_staff.project_registry.find_by_id(self.client_request.project_id)
            if self.project is None:
                raise ValueError(f"Linked project {self.client_request.project_id} not found in registry.")
        else:
            # Otherwise create it
            project = self.chief_of_staff.create_project(
                title=self.client_request.title,
                client=self.client_request.client_name,
                description=self.client_request.problem_statement,
            )
            self.chief_of_staff.register_project(project)
            self.client_request.link_project(project.id, actor="workflow")
            self.project = project
            
        # Make sure project is active
        project_status = getattr(self.project.status, "value", self.project.status)
        if project_status != ProjectStatus.ACTIVE.value:
            self.project.update_status(ProjectStatus.ACTIVE, actor="workflow")
            
        return self.project

    def assign_initial_work(self) -> None:
        if self.project is None or self.client_request is None:
            raise ValueError("Project or client request is missing.")
            
        # Load any existing work orders
        self.work_orders = list(self.project.work_orders)
        
        # If no work orders exist, create the initial ones
        if not self.work_orders:
            # Map ClientRequestPriority to WorkOrderPriority
            priority_map = {
                ClientRequestPriority.LOW: WorkOrderPriority.LOW,
                ClientRequestPriority.MEDIUM: WorkOrderPriority.MEDIUM,
                ClientRequestPriority.HIGH: WorkOrderPriority.HIGH,
                ClientRequestPriority.CRITICAL: WorkOrderPriority.CRITICAL,
            }
            client_priority = getattr(self.client_request.priority, "value", self.client_request.priority)
            wo_priority = priority_map.get(client_priority, WorkOrderPriority.MEDIUM)
            
            work_order = self.chief_of_staff.create_work_order(
                project_id=self.project.id,
                title="Engagement Kickoff",
                objective="Prepare client proposal and engagement terms.",
                priority=wo_priority,
            )
            self.work_orders.append(work_order)
            
        # Attempt to assign unassigned work orders
        for work_order in self.work_orders:
            wo_status = getattr(work_order.status, "value", work_order.status)
            if wo_status == WorkOrderStatus.CREATED.value:
                # Discover available workers
                available_workers = self.chief_of_staff.worker_registry.list_available()
                if available_workers:
                    worker = available_workers[0]
                    self.chief_of_staff.assign_work_order(
                        work_order_id=work_order.id,
                        worker_id=worker.id,
                        assigned_by="workflow",
                    )
                    self.assignments[work_order.id] = worker.id

    def monitor_execution(self) -> None:
        if self.project is None:
            return
            
        # Sync current state from business objects
        self.work_orders = list(self.project.work_orders)
        self.deliverables = list(self.project.deliverables)
        
        # Update assignments dictionary from existing work orders
        for wo in self.work_orders:
            if wo.assigned_to:
                self.assignments[wo.id] = wo.assigned_to

        # Check for deliverables that can complete pending work orders
        for wo in self.work_orders:
            wo_status = getattr(wo.status, "value", wo.status)
            if wo_status not in {WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value}:
                # If there's an approved deliverable for this work order, complete it
                for deliverable in self.deliverables:
                    del_status = getattr(deliverable.status, "value", deliverable.status)
                    if deliverable.work_order_id == wo.id and del_status == DeliverableStatus.APPROVED.value:
                        self.chief_of_staff.complete_work_order(wo.id, deliverable.id)
                        break

        # Calculate requirements for CEO attention
        self._items_requiring_ceo_attention = []
        for wo in self.work_orders:
            wo_status = getattr(wo.status, "value", wo.status)
            wo_priority = getattr(wo.priority, "value", wo.priority)
            if wo_status != WorkOrderStatus.COMPLETED.value and wo_priority in {WorkOrderPriority.HIGH.value, WorkOrderPriority.CRITICAL.value}:
                self._items_requiring_ceo_attention.append(wo.summary())

        # Check if the project is completed
        proj_status = getattr(self.project.status, "value", self.project.status)
        
        # If all work orders are completed, let's complete the project if it isn't already completed
        all_completed = len(self.work_orders) > 0 and all(
            getattr(wo.status, "value", wo.status) == WorkOrderStatus.COMPLETED.value
            for wo in self.work_orders
        )
        if all_completed and proj_status != ProjectStatus.COMPLETED.value:
            self.project.update_status(ProjectStatus.COMPLETED, actor="workflow")
            proj_status = ProjectStatus.COMPLETED.value

        # Update workflow state
        if proj_status == ProjectStatus.COMPLETED.value:
            self.close_workflow()
        else:
            self.state = WorkflowState.WAITING

    def close_workflow(self) -> None:
        if self.project and getattr(self.project.status, "value", self.project.status) == ProjectStatus.COMPLETED.value:
            self.state = WorkflowState.COMPLETED
            self._log_state_change("close_workflow", "system", "completed")
        else:
            self.state = WorkflowState.FAILED
            self._log_state_change("close_workflow", "system", "failed")

    def generate_summary(self) -> dict[str, Any]:
        return {
            "workflow_state": self.state.value if isinstance(self.state, Enum) else self.state,
            "client_request": self.client_request.summary() if self.client_request else None,
            "project": self.project.summary() if self.project else None,
            "work_orders_created": [wo.summary() for wo in self.work_orders],
            "assignments_made": dict(self.assignments),
            "deliverables_collected": [d.summary() for d in self.deliverables],
            "completion_status": "Completed" if self.state == WorkflowState.COMPLETED else "Pending" if self.state == WorkflowState.WAITING else "Failed" if self.state == WorkflowState.FAILED else "Cancelled" if self.state == WorkflowState.CANCELLED else "Not Started",
            "items_requiring_ceo_attention": list(self._items_requiring_ceo_attention),
        }

    def _log_state_change(self, action: str, actor: str, result: str) -> None:
        LOGGER.info(
            "timestamp=%s workflow_state=%s action=%s actor=%s result=%s",
            datetime.now(timezone.utc).isoformat(),
            self.state.value if isinstance(self.state, Enum) else self.state,
            action,
            actor,
            result,
        )
