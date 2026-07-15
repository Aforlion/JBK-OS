import unittest
from typing import Any

from core.project import Project
from core.work_order import WorkOrder, WorkOrderStatus
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.skill_registry import SkillRegistry
from core.executive import Executive
from core.skill import Skill
from core.execution_report import ExecutionReport
from core.work_execution_orchestrator import WorkExecutionOrchestrator


class MockExecutionPlanner:
    def __init__(self, skill_id: str, engine_name: str) -> None:
        self.skill_id = skill_id
        self.engine_name = engine_name

    def get_recommendation(self, work_order: WorkOrder) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "engine_name": self.engine_name,
        }


class TestWorkExecutionOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = WorkExecutionOrchestrator()
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.skill_registry = SkillRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )
        self.planner = MockExecutionPlanner(skill_id="SKL-0001", engine_name="Antigravity")

        # Create project and worker
        self.project = self.chief_of_staff.create_project(
            project_id="PROJ-0001",
            title="WMS Build",
            client="Global Log",
            description="Warehouse Management",
        )
        self.chief_of_staff.register_project(self.project)

        self.worker = Executive(
            executive_id="EXEC-0001",
            title="Dev Lead",
            mission="Write backend loops",
        )
        self.worker_registry.register(self.worker)

        # Create Work Order
        self.work_order = self.chief_of_staff.create_work_order(
            project_id="PROJ-0001",
            title="DB Setup",
            objective="Configure Postgres",
        )
        self.chief_of_staff.assign_work_order(self.work_order.id, "EXEC-0001")
        setattr(self.work_order, "dependencies", [])

        # Create Skill
        self.skill = Skill(
            skill_id="SKL-0001",
            name="Db Config",
            description="Database skills",
            owner_id="EXEC-0001",
            department="Technology",
            execution_engine="Postgres",
            capabilities=["DB Integration"],
            inputs=[],
            outputs=[],
            version="1.0"
        )
        self.skill_registry.register(self.skill)

    def test_invalid_orchestration_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.orchestrator.execute_work_order(None, self.project, self.skill_registry, self.planner, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.orchestrator.execute_work_order(self.work_order, None, self.skill_registry, self.planner, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.orchestrator.execute_work_order(self.work_order, self.project, None, self.planner, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.orchestrator.execute_work_order(self.work_order, self.project, self.skill_registry, None, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.orchestrator.execute_work_order(self.work_order, self.project, self.skill_registry, self.planner, None)  # type: ignore

    def test_execution_success(self) -> None:
        report = self.orchestrator.execute_work_order(
            self.work_order, self.project, self.skill_registry, self.planner, self.chief_of_staff
        )
        self.assertIsInstance(report, ExecutionReport)
        self.assertEqual(report.status, "COMPLETED")
        self.assertEqual(report.engine_name, "Antigravity")
        
        # Verify WorkOrder status transitions to COMPLETED
        self.assertEqual(self.work_order.status, WorkOrderStatus.COMPLETED)
        
        # Verify deliverable exists
        self.assertIsNotNone(self.work_order.deliverable_id)
        self.assertIn("deliverable_id", report.outputs)

    def test_dependency_blocking(self) -> None:
        # Create a dependent work order
        dep_wo = self.chief_of_staff.create_work_order(
            project_id="PROJ-0001",
            title="Design Phase",
            objective="Requirements specs",
        )
        # Link dependency
        setattr(self.work_order, "dependencies", [dep_wo.id])
        
        # dep_wo is in CREATED status (not COMPLETED). Orchestration should WAIT.
        report = self.orchestrator.execute_work_order(
            self.work_order, self.project, self.skill_registry, self.planner, self.chief_of_staff
        )
        self.assertEqual(report.status, "WAITING")
        self.assertEqual(self.work_order.status, "WAITING")

    def test_skill_unavailability_crashes(self) -> None:
        # Disable the skill
        self.skill.update_status("DISABLED")
        
        report = self.orchestrator.execute_work_order(
            self.work_order, self.project, self.skill_registry, self.planner, self.chief_of_staff
        )
        self.assertEqual(report.status, "FAILED")
        self.assertTrue(any("not available" in e for e in report.errors))

    def test_serialization(self) -> None:
        report = self.orchestrator.execute_work_order(
            self.work_order, self.project, self.skill_registry, self.planner, self.chief_of_staff
        )
        summary = report.summary()
        self.assertEqual(summary["report_id"], report.report_id)
        self.assertEqual(summary["status"], "COMPLETED")
        
        to_dict_out = report.to_dict()
        self.assertEqual(to_dict_out["report_id"], report.report_id)
        self.assertEqual(to_dict_out["work_order_id"], self.work_order.id)
