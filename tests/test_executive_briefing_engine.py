import unittest

from core.executive_briefing_engine import ExecutiveBriefingEngine
from core.client_request import ClientRequest, ClientRequestPriority
from core.project import Project, ProjectStatus
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.chief_of_staff import ChiefOfStaff
from core.executive import Executive, ExecutiveStatus
from core.work_order import WorkOrder, WorkOrderStatus
from core.deliverable import Deliverable, DeliverableStatus
from core.business_process_workflow import BusinessProcessWorkflow, WorkflowState


class TestExecutiveBriefingEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )
        self.engine = ExecutiveBriefingEngine(self.chief_of_staff)

    def create_project(self, title: str, client: str, status: str = "ACTIVE") -> Project:
        project = self.chief_of_staff.create_project(
            title=title, client=client, description="Test project description."
        )
        self.chief_of_staff.register_project(project)
        project.update_status(status)
        return project

    def create_worker(self, name: str, role: str, status: str = "AVAILABLE") -> Executive:
        worker = Executive(
            title=role, mission="Achieve objectives.", status=status
        )
        self.worker_registry.register(worker)
        return worker

    def create_request(self, client: str, title: str, priority: str = "MEDIUM") -> ClientRequest:
        return ClientRequest(
            client_name=client,
            organization=client + " Org",
            contact_person="Contact Person",
            contact_email="email@test.com",
            contact_phone="12345678",
            industry="IT",
            title=title,
            problem_statement="Problem description.",
            desired_outcome="Success outcome.",
            priority=priority,
        )

    def test_instantiation_without_chief_of_staff(self) -> None:
        with self.assertRaises(ValueError):
            ExecutiveBriefingEngine(None)

    def test_generate_summary_basic(self) -> None:
        # Initially empty
        summary = self.engine.generate_summary()
        self.assertEqual(summary["total_executives"], 0)
        self.assertEqual(summary["available_executives"], 0)
        self.assertEqual(summary["busy_executives"], 0)
        self.assertEqual(summary["projects"], 0)
        self.assertEqual(summary["work_orders"], 0)
        self.assertEqual(summary["deliverables"], 0)
        self.assertEqual(summary["client_requests"], 0)
        self.assertEqual(summary["operational_health"], "HEALTHY")
        self.assertEqual(summary["ceo_attention_count"], 0)

    def test_generate_summary_with_entities(self) -> None:
        self.create_worker("Alice", "Engineer", "AVAILABLE")
        self.create_worker("Bob", "Manager", "BUSY")
        project = self.create_project("Project Alpha", "Client A", "ACTIVE")
        
        self.chief_of_staff.create_work_order(
            project_id=project.id,
            title="Task 1",
            objective="Do task 1",
        )
        req = self.create_request("Client B", "Need help")
        engine = ExecutiveBriefingEngine(self.chief_of_staff, client_requests=[req])

        summary = engine.generate_summary()
        self.assertEqual(summary["total_executives"], 2)
        self.assertEqual(summary["available_executives"], 1)
        self.assertEqual(summary["busy_executives"], 1)
        self.assertEqual(summary["projects"], 1)
        self.assertEqual(summary["work_orders"], 1)
        self.assertEqual(summary["client_requests"], 1)

    def test_ceo_attention_items_detection(self) -> None:
        project = self.create_project("Project Alpha", "Client A", "ACTIVE")
        # 1. Project without assigned work
        attention = self.engine.generate_ceo_attention_items()
        self.assertTrue(any(item["type"] == "PROJECT_WITHOUT_ASSIGNED_WORK" for item in attention))

        # 2. Executive Suspended
        suspended_worker = self.create_worker("Charlie", "Operator", "SUSPENDED")
        attention = self.engine.generate_ceo_attention_items()
        self.assertTrue(any(item["type"] == "SUSPENDED_EXECUTIVE" and item["id"] == suspended_worker.id for item in attention))

        # 3. Unassigned WorkOrder
        wo = self.chief_of_staff.create_work_order(
            project_id=project.id,
            title="Kickoff Task",
            objective="Kick off project",
        )
        attention = self.engine.generate_ceo_attention_items()
        self.assertTrue(any(item["type"] == "UNASSIGNED_WORK_ORDER" and item["id"] == wo.id for item in attention))

        # 4. Critical priority request
        req = self.create_request("Client A", "Urgent Request", priority=ClientRequestPriority.CRITICAL)
        engine = ExecutiveBriefingEngine(self.chief_of_staff, client_requests=[req])
        attention = engine.generate_ceo_attention_items()
        self.assertTrue(any(item["type"] == "CRITICAL_CLIENT_REQUEST" and item["id"] == req.id for item in attention))

        # 5. Rejected Deliverable
        deliverable = Deliverable(
            project_id=project.id,
            work_order_id=wo.id,
            title="Spec Doc",
            author="Charlie",
        )
        deliverable.status = DeliverableStatus.REJECTED
        project.add_deliverable(deliverable)
        attention = engine.generate_ceo_attention_items()
        self.assertTrue(any(item["type"] == "REJECTED_DELIVERABLE" and item["id"] == deliverable.id for item in attention))

    def test_operational_health_rules(self) -> None:
        # No active projects -> HEALTHY
        self.assertEqual(self.engine.generate_summary()["operational_health"], "HEALTHY")

        # Create active project, but no workers -> WARNING
        project = self.create_project("Project Alpha", "Client A", "ACTIVE")
        self.assertEqual(self.engine.generate_summary()["operational_health"], "HEALTHY") # active project exists, no registered workers so available count == 0 and total == 0, health is healthy.
        
        # Register workers, but available = 0 -> WARNING
        worker = self.create_worker("Bob", "Manager", "BUSY")
        self.assertEqual(self.engine.generate_summary()["operational_health"], "WARNING")

        # Make worker available -> HEALTHY
        worker.status = ExecutiveStatus.AVAILABLE
        self.assertEqual(self.engine.generate_summary()["operational_health"], "HEALTHY")

        # Multiple blocked projects (active but no work orders) -> WARNING
        self.create_project("Project Beta", "Client B", "ACTIVE")
        self.assertEqual(self.engine.generate_summary()["operational_health"], "WARNING")
