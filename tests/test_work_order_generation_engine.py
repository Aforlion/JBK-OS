import unittest

from core.project import Project
from core.resource_allocation_plan import ResourceAllocationPlan
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.executive import Executive, ExecutiveStatus
from core.work_order import WorkOrder
from core.work_order_generation_engine import WorkOrderGenerationEngine
from core.work_order_generation_report import WorkOrderGenerationReport


class TestWorkOrderGenerationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = WorkOrderGenerationEngine()
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )

        # Set up project
        self.project = self.chief_of_staff.create_project(
            project_id="PROJ-0001",
            title="E-commerce Build",
            client="Acme",
            description="Build online storefront",
        )
        self.chief_of_staff.register_project(self.project)

        # Set up workers
        self.worker_tech = Executive(
            executive_id="EXEC-0001",
            title="Dev Lead",
            mission="Code baseline",
        )
        self.worker_registry.register(self.worker_tech)

        # Create allocation plan
        self.plan = ResourceAllocationPlan(
            allocation_id="ALL-0001",
            project_id="PROJ-0001",
            assignments=[
                {
                    "task_id": "TSK-01",
                    "worker_id": "EXEC-0001",
                    "worker_name": "Dev Lead",
                    "department": "Technology",
                    "confidence": 1.0,
                    "capability_match": ["API Integration"],
                    "estimated_load": 30.0,
                    "rationale": "Capabilities match",
                    "title": "Backend Setup",
                    "description": "Install database",
                    "priority": "HIGH",
                    "dependencies": []
                }
            ],
            unassigned_tasks=[
                {
                    "task_id": "TSK-02",
                    "title": "Staff Training",
                    "recommended_capabilities": ["Training"]
                }
            ],
            workload_summary={"EXEC-0001": 30.0},
            utilization={},
            warnings=[]
        )

    def test_invalid_generation_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.generate_work_orders(None, self.plan, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.generate_work_orders(self.project, None, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.generate_work_orders(self.project, self.plan, None)  # type: ignore

    def test_project_id_mismatch(self) -> None:
        mismatch_project = Project(project_id="PROJ-MISMATCH", title="T1", client="C1", description="D1")
        with self.assertRaises(ValueError):
            self.engine.generate_work_orders(mismatch_project, self.plan, self.chief_of_staff)

    def test_generation_success(self) -> None:
        report = self.engine.generate_work_orders(self.project, self.plan, self.chief_of_staff)
        self.assertIsInstance(report, WorkOrderGenerationReport)
        self.assertEqual(report.project_id, "PROJ-0001")
        
        # Verify exactly 1 Work Order is created
        self.assertEqual(len(self.project.work_orders), 1)
        wo = self.project.work_orders[0]
        self.assertEqual(wo.title, "Backend Setup")
        self.assertEqual(wo.objective, "Install database")
        self.assertEqual(wo.assigned_to, "EXEC-0001")
        
        # Verify dynamic attributes
        self.assertEqual(getattr(wo, "estimated_hours", None), 30.0)
        self.assertEqual(getattr(wo, "required_capabilities", None), ["API Integration"])
        
        # Verify skipped tasks
        self.assertEqual(len(report.skipped_tasks), 1)
        self.assertEqual(report.skipped_tasks[0]["task_id"], "TSK-02")
        self.assertEqual(report.skipped_tasks[0]["status"], "PENDING_RESOURCE")

    def test_atomicity_rollback(self) -> None:
        # Create an allocation containing a worker ID that is NOT registered (EXEC-9999)
        invalid_plan = ResourceAllocationPlan(
            allocation_id="ALL-0002",
            project_id="PROJ-0001",
            assignments=[
                {
                    "task_id": "TSK-01",
                    "worker_id": "EXEC-0001",
                    "worker_name": "Dev Lead",
                    "department": "Technology",
                    "confidence": 1.0,
                    "capability_match": ["API Integration"],
                    "estimated_load": 30.0,
                    "rationale": "Capabilities match",
                    "title": "Backend Setup",
                    "description": "Install database",
                    "priority": "HIGH",
                    "dependencies": []
                },
                {
                    "task_id": "TSK-02",
                    "worker_id": "EXEC-9999", # Invalid unregistered worker
                    "worker_name": "Ghost",
                    "department": "Ops",
                    "confidence": 1.0,
                    "capability_match": [],
                    "estimated_load": 10.0,
                    "rationale": "None",
                    "title": "Manual Setup",
                    "description": "Ghost work",
                    "priority": "LOW",
                    "dependencies": []
                }
            ],
            unassigned_tasks=[],
            workload_summary={},
            utilization={},
            warnings=[]
        )
        
        # Try generating: should throw ValueError and leave project.work_orders completely empty
        # (rolling back TSK-01 creation)
        with self.assertRaises(ValueError):
            self.engine.generate_work_orders(self.project, invalid_plan, self.chief_of_staff)
            
        self.assertEqual(len(self.project.work_orders), 0)

    def test_serialization(self) -> None:
        report = self.engine.generate_work_orders(self.project, self.plan, self.chief_of_staff)
        summary = report.summary()
        self.assertEqual(summary["generation_id"], report.generation_id)
        self.assertEqual(summary["created_work_orders_count"], 1)
        self.assertEqual(summary["skipped_tasks_count"], 1)
        
        to_dict_out = report.to_dict()
        self.assertEqual(to_dict_out["generation_id"], report.generation_id)
        self.assertEqual(len(to_dict_out["created_work_orders"]), 1)
