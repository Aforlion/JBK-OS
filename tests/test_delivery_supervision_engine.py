import unittest

from core.project import Project
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.executive import Executive
from core.work_order import WorkOrder, WorkOrderStatus
from core.delivery_supervision_engine import DeliverySupervisionEngine
from core.delivery_status_report import DeliveryStatusReport


class TestDeliverySupervisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DeliverySupervisionEngine()
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )

        # Register workers
        self.worker1 = Executive(executive_id="EXEC-0001", title="Lead Dev", mission="Write code")
        self.worker2 = Executive(executive_id="EXEC-0002", title="Sysops", mission="Deploy code")
        self.worker_registry.register(self.worker1)
        self.worker_registry.register(self.worker2)

        # Create active project
        self.project = self.chief_of_staff.create_project(
            project_id="PROJ-0001",
            title="E-Shop Backend",
            client="Tech Corp",
            description="Build loops",
        )
        self.chief_of_staff.register_project(self.project)

    def test_invalid_supervision_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.supervise_project(None, self.worker_registry)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.supervise_project(self.project, None)  # type: ignore

    def test_healthy_project(self) -> None:
        # Create work order with low utilization and status COMPLETED
        wo = self.chief_of_staff.create_work_order(self.project.id, "Setup Git", "objective")
        self.chief_of_staff.assign_work_order(wo.id, "EXEC-0001")
        setattr(wo, "estimated_hours", 10.0)
        wo.complete(actor="system")

        report = self.engine.supervise_project(self.project, self.worker_registry)
        self.assertIsInstance(report, DeliveryStatusReport)
        self.assertEqual(report.health_status, "HEALTHY")
        self.assertEqual(len(report.completed_work), 1)
        self.assertEqual(len(report.blockers), 0)

    def test_watch_project_single_blocker(self) -> None:
        # Create a work order with status WAITING (single blocker)
        wo = self.chief_of_staff.create_work_order(self.project.id, "Design DB", "objective")
        self.chief_of_staff.assign_work_order(wo.id, "EXEC-0001")
        setattr(wo, "estimated_hours", 10.0)
        wo.status = "WAITING"

        report = self.engine.supervise_project(self.project, self.worker_registry)
        self.assertEqual(report.health_status, "WATCH")
        self.assertEqual(len(report.blockers), 1)

    def test_at_risk_project_overload(self) -> None:
        # Assign > 40 hours to worker1 (overload)
        wo1 = self.chief_of_staff.create_work_order(self.project.id, "API Dev", "objective")
        self.chief_of_staff.assign_work_order(wo1.id, "EXEC-0001")
        setattr(wo1, "estimated_hours", 45.0)

        report = self.engine.supervise_project(self.project, self.worker_registry)
        self.assertEqual(report.health_status, "AT_RISK")
        self.assertEqual(len(report.ceo_attention_items), 1)
        self.assertEqual(report.ceo_attention_items[0]["type"], "WORKER_OVERLOADED")

    def test_critical_project_failed_execution(self) -> None:
        # Work order in status FAILED
        wo = self.chief_of_staff.create_work_order(self.project.id, "Deploy Sandbox", "objective")
        self.chief_of_staff.assign_work_order(wo.id, "EXEC-0002")
        wo.status = "FAILED"

        report = self.engine.supervise_project(self.project, self.worker_registry)
        self.assertEqual(report.health_status, "CRITICAL")
        self.assertEqual(len(report.failed_work), 1)
        self.assertEqual(len(report.ceo_attention_items), 1)
        self.assertEqual(report.ceo_attention_items[0]["type"], "EXECUTION_FAILURE")

    def test_serialization(self) -> None:
        report = self.engine.supervise_project(self.project, self.worker_registry)
        summary = report.summary()
        self.assertEqual(summary["report_id"], report.report_id)
        
        to_dict_out = report.to_dict()
        self.assertEqual(to_dict_out["report_id"], report.report_id)
