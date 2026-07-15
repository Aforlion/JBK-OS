import unittest
from unittest.mock import MagicMock

from core.business_process_workflow import BusinessProcessWorkflow, WorkflowState
from core.client_request import ClientRequest, ClientRequestStatus, ClientRequestPriority
from core.project import Project, ProjectStatus
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.chief_of_staff import ChiefOfStaff
from core.executive import Executive, ExecutiveStatus
from core.work_order import WorkOrder, WorkOrderPriority, WorkOrderStatus
from core.deliverable import Deliverable, DeliverableStatus


class TestBusinessProcessWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )
        self.workflow = BusinessProcessWorkflow(self.chief_of_staff)
        
        # Helper worker
        self.worker = Executive(
            executive_id="EXEC-0002",
            title="Senior Engineer",
            mission="Deliver code.",
        )
        self.worker_registry.register(self.worker)

    def create_valid_request(self) -> ClientRequest:
        return ClientRequest(
            client_name="Acme Corp",
            organization="Acme Industries",
            contact_person="John Doe",
            contact_email="john@acme.com",
            contact_phone="12345678",
            industry="Software",
            title="Setup Infrastructure",
            problem_statement="Needs cloud server setup.",
            desired_outcome="Production ready cluster.",
            priority=ClientRequestPriority.HIGH,
        )

    def test_workflow_initial_state(self) -> None:
        self.assertEqual(self.workflow.state, WorkflowState.NOT_STARTED)
        self.assertIsNone(self.workflow.client_request)
        self.assertIsNone(self.workflow.project)
        self.assertEqual(self.workflow.work_orders, [])

    def test_workflow_fails_with_no_chief_of_staff(self) -> None:
        with self.assertRaises(ValueError):
            BusinessProcessWorkflow(None)

    def test_start_with_invalid_args(self) -> None:
        with self.assertRaises(ValueError):
            self.workflow.start(None)

    def test_workflow_start_new_request_approved_and_processed(self) -> None:
        request = self.create_valid_request()
        self.assertEqual(request.status, ClientRequestStatus.NEW)

        self.workflow.start(request)

        # It should approve the request
        self.assertEqual(request.status, ClientRequestStatus.PROJECT_CREATED)
        self.assertIsNotNone(request.project_id)

        # It should create project and mark it active
        self.assertIsNotNone(self.workflow.project)
        self.assertEqual(self.workflow.project.status, ProjectStatus.ACTIVE)
        self.assertEqual(self.workflow.project.client, "Acme Corp")

        # It should create an initial work order and assign it to available worker
        self.assertEqual(len(self.workflow.work_orders), 1)
        wo = self.workflow.work_orders[0]
        self.assertEqual(wo.title, "Engagement Kickoff")
        self.assertEqual(wo.status, WorkOrderStatus.ASSIGNED)
        self.assertEqual(wo.assigned_to, "EXEC-0002")

        # Workflow state should be WAITING
        self.assertEqual(self.workflow.state, WorkflowState.WAITING)

    def test_workflow_start_already_rejected(self) -> None:
        request = self.create_valid_request()
        request.reject()
        self.assertEqual(request.status, ClientRequestStatus.REJECTED)

        self.workflow.start(request)
        self.assertEqual(self.workflow.state, WorkflowState.FAILED)

    def test_workflow_start_already_withdrawn(self) -> None:
        request = self.create_valid_request()
        request.withdraw()
        self.assertEqual(request.status, ClientRequestStatus.WITHDRAWN)

        self.workflow.start(request)
        self.assertEqual(self.workflow.state, WorkflowState.CANCELLED)

    def test_workflow_resume_and_complete_with_deliverable(self) -> None:
        request = self.create_valid_request()
        self.workflow.start(request)
        
        # Confirm it is waiting
        self.assertEqual(self.workflow.state, WorkflowState.WAITING)
        wo = self.workflow.work_orders[0]
        project = self.workflow.project
        
        # Simulate worker completing work order and creating an approved deliverable
        # Deliverable requires: title, project_id, work_order_id, content
        deliverable = Deliverable(
            project_id=project.id,
            work_order_id=wo.id,
            title="Proposal Draft Deliverable",
            author="EXEC-0002",
            content="Proposal is drafted.",
        )
        deliverable.approve(actor="client")
        
        self.chief_of_staff.collect_deliverable(deliverable)
        
        # Resume/Monitor workflow
        self.workflow.monitor_execution()
        
        # Work order should be completed
        self.assertEqual(wo.status, WorkOrderStatus.COMPLETED)
        # Project should be completed
        self.assertEqual(project.status, ProjectStatus.COMPLETED)
        # Workflow state should be COMPLETED
        self.assertEqual(self.workflow.state, WorkflowState.COMPLETED)

    def test_generate_summary_structure(self) -> None:
        request = self.create_valid_request()
        self.workflow.start(request)
        
        summary = self.workflow.generate_summary()
        
        self.assertIn("workflow_state", summary)
        self.assertIn("client_request", summary)
        self.assertIn("project", summary)
        self.assertIn("work_orders_created", summary)
        self.assertIn("assignments_made", summary)
        self.assertIn("deliverables_collected", summary)
        self.assertIn("completion_status", summary)
        self.assertIn("items_requiring_ceo_attention", summary)
        
        self.assertEqual(summary["workflow_state"], "WAITING")
        self.assertEqual(summary["completion_status"], "Pending")
        self.assertEqual(len(summary["work_orders_created"]), 1)
        self.assertEqual(summary["assignments_made"], {self.workflow.work_orders[0].id: "EXEC-0002"})

    def test_ceo_attention_for_high_priority_uncompleted(self) -> None:
        request = self.create_valid_request() # priority is HIGH
        self.workflow.start(request)
        
        summary = self.workflow.generate_summary()
        # Initial work order should match high priority
        self.assertEqual(len(summary["items_requiring_ceo_attention"]), 1)
        self.assertEqual(summary["items_requiring_ceo_attention"][0]["id"], self.workflow.work_orders[0].id)
