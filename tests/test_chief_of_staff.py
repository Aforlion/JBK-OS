import unittest

from core.chief_of_staff import ChiefOfStaff
from core.deliverable import Deliverable, DeliverableStatus
from core.executive import Executive, ExecutiveStatus
from core.project import ProjectStatus
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.work_order import WorkOrderPriority, WorkOrderStatus


class ChiefOfStaffTest(unittest.TestCase):
    def setUp(self):
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )

    def test_chief_of_staff_can_be_instantiated(self):
        self.assertIs(self.chief_of_staff.worker_registry, self.worker_registry)
        self.assertIs(self.chief_of_staff.project_registry, self.project_registry)

    def test_projects_can_be_created_and_registered(self):
        project = self.chief_of_staff.create_project(
            project_id="PROJ-0101",
            title="Client Workflow",
            client="JBK",
            description="Create the first client workflow.",
        )

        registered_project = self.chief_of_staff.register_project(project)

        self.assertIs(registered_project, project)
        self.assertIs(self.project_registry.find_by_id("PROJ-0101"), project)

    def test_work_orders_can_be_created_for_registered_projects(self):
        project = self.chief_of_staff.create_project(
            project_id="PROJ-0102",
            title="WorkOrder Project",
            client="JBK",
            description="Create WorkOrders.",
        )
        self.chief_of_staff.register_project(project)

        work_order = self.chief_of_staff.create_work_order(
            project_id="PROJ-0102",
            work_order_id="WO-0101",
            title="Draft Workflow",
            objective="Draft the workflow.",
            priority=WorkOrderPriority.HIGH,
        )

        self.assertEqual(work_order.project_id, "PROJ-0102")
        self.assertEqual(work_order.priority, WorkOrderPriority.HIGH)
        self.assertEqual(project.work_orders, [work_order])

    def test_workers_are_discovered_through_worker_registry_for_assignment(self):
        project = self.chief_of_staff.create_project(
            project_id="PROJ-0103",
            title="Assignment Project",
            client="JBK",
            description="Assign WorkOrders.",
        )
        worker = Executive(
            executive_id="EXEC-0101",
            title="Chief Product Officer",
            mission="Own product outcomes.",
        )
        self.chief_of_staff.register_project(project)
        self.worker_registry.register(worker)
        work_order = self.chief_of_staff.create_work_order(
            project_id="PROJ-0103",
            work_order_id="WO-0102",
            title="Prepare PRD",
            objective="Prepare a product requirements document.",
        )

        assigned_work_order = self.chief_of_staff.assign_work_order(
            work_order_id="WO-0102",
            worker_id="EXEC-0101",
            assigned_by="EXEC-0001",
        )

        self.assertIs(assigned_work_order, work_order)
        self.assertEqual(work_order.status, WorkOrderStatus.ASSIGNED)
        self.assertEqual(work_order.assigned_to, "EXEC-0101")
        self.assertEqual(worker.assigned_work_orders, [work_order])

    def test_assigning_work_order_requires_registered_worker(self):
        project = self.chief_of_staff.create_project(
            project_id="PROJ-0104",
            title="Missing Worker Project",
            client="JBK",
            description="Verify worker discovery.",
        )
        self.chief_of_staff.register_project(project)
        self.chief_of_staff.create_work_order(
            project_id="PROJ-0104",
            work_order_id="WO-0103",
            title="Unassigned Work",
            objective="Fail assignment without worker.",
        )

        with self.assertRaisesRegex(ValueError, "Worker not found"):
            self.chief_of_staff.assign_work_order("WO-0103", "EXEC-9999")

    def test_deliverables_can_be_collected_without_creating_them(self):
        project, work_order, _worker = self._create_assigned_work_order(
            project_id="PROJ-0105",
            work_order_id="WO-0104",
            worker_id="EXEC-0102",
        )
        deliverable = Deliverable(
            deliverable_id="DEL-0101",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Workflow Report",
            author="EXEC-0102",
        )

        collected_deliverable = self.chief_of_staff.collect_deliverable(deliverable)

        self.assertIs(collected_deliverable, deliverable)
        self.assertEqual(project.deliverables, [deliverable])
        self.assertEqual(work_order.deliverable_id, "DEL-0101")

    def test_work_order_cannot_complete_without_approved_deliverable(self):
        project, work_order, _worker = self._create_assigned_work_order(
            project_id="PROJ-0106",
            work_order_id="WO-0105",
            worker_id="EXEC-0103",
        )
        deliverable = Deliverable(
            deliverable_id="DEL-0102",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Draft Report",
            author="EXEC-0103",
        )
        self.chief_of_staff.collect_deliverable(deliverable)

        with self.assertRaisesRegex(ValueError, "APPROVED Deliverable"):
            self.chief_of_staff.complete_work_order("WO-0105", "DEL-0102")

        self.assertEqual(work_order.status, WorkOrderStatus.ASSIGNED)

    def test_work_order_can_complete_with_approved_deliverable(self):
        project, work_order, worker = self._create_assigned_work_order(
            project_id="PROJ-0107",
            work_order_id="WO-0106",
            worker_id="EXEC-0104",
        )
        deliverable = Deliverable(
            deliverable_id="DEL-0103",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Approved Report",
            author="EXEC-0104",
        )
        deliverable.approve()
        self.chief_of_staff.collect_deliverable(deliverable)

        completed_work_order = self.chief_of_staff.complete_work_order(
            work_order_id="WO-0106",
            deliverable_id="DEL-0103",
        )

        self.assertIs(completed_work_order, work_order)
        self.assertEqual(work_order.status, WorkOrderStatus.COMPLETED)
        self.assertIn(work_order, worker.completed_work_orders)
        self.assertNotIn(work_order, worker.assigned_work_orders)

    def test_completed_work_orders_are_read_only_to_chief_of_staff(self):
        project, work_order, _worker = self._create_assigned_work_order(
            project_id="PROJ-0108",
            work_order_id="WO-0107",
            worker_id="EXEC-0105",
        )
        deliverable = Deliverable(
            deliverable_id="DEL-0104",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Approved Output",
            author="EXEC-0105",
        )
        deliverable.approve()
        self.chief_of_staff.collect_deliverable(deliverable)
        self.chief_of_staff.complete_work_order("WO-0107", "DEL-0104")

        with self.assertRaisesRegex(ValueError, "read-only"):
            self.chief_of_staff.assign_work_order("WO-0107", "EXEC-0105")

    def test_cancelled_work_orders_are_read_only_to_chief_of_staff(self):
        project, work_order, _worker = self._create_assigned_work_order(
            project_id="PROJ-0109",
            work_order_id="WO-0108",
            worker_id="EXEC-0106",
        )
        work_order.cancel()
        deliverable = Deliverable(
            deliverable_id="DEL-0105",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Late Output",
            author="EXEC-0106",
        )

        with self.assertRaisesRegex(ValueError, "read-only"):
            self.chief_of_staff.collect_deliverable(deliverable)

    def test_monitor_project_returns_structured_progress(self):
        project, work_order, _worker = self._create_assigned_work_order(
            project_id="PROJ-0110",
            work_order_id="WO-0109",
            worker_id="EXEC-0107",
        )

        progress = self.chief_of_staff.monitor_project(project.id)

        self.assertEqual(progress["project"], project.summary())
        self.assertEqual(progress["work_orders"], [work_order.summary()])
        self.assertEqual(progress["deliverables"], [])

    def test_generate_executive_brief_returns_required_sections(self):
        project, work_order, worker = self._create_assigned_work_order(
            project_id="PROJ-0111",
            work_order_id="WO-0110",
            worker_id="EXEC-0108",
            project_status=ProjectStatus.ACTIVE,
            priority=WorkOrderPriority.CRITICAL,
        )
        worker.accept_work_order(work_order)
        deliverable = Deliverable(
            deliverable_id="DEL-0106",
            project_id=project.id,
            work_order_id=work_order.id,
            title="Approved Brief",
            author=worker.id,
        )
        deliverable.approve()
        self.chief_of_staff.collect_deliverable(deliverable)
        self.chief_of_staff.complete_work_order("WO-0110", "DEL-0106")

        brief = self.chief_of_staff.generate_executive_brief()

        self.assertEqual(brief["projects_in_progress"], [project.summary()])
        self.assertEqual(brief["completed_work_orders"], [work_order.summary()])
        self.assertEqual(brief["pending_work_orders"], [])
        self.assertEqual(brief["available_workers"], [worker.to_dict()])
        self.assertEqual(brief["busy_workers"], [])
        self.assertEqual(brief["completed_deliverables"], [deliverable.summary()])
        self.assertEqual(brief["items_requiring_ceo_attention"], [])

    def test_project_summary_uses_project_registry_discovery(self):
        project = self.chief_of_staff.create_project(
            project_id="PROJ-0112",
            title="Summary Project",
            client="JBK",
            description="Summarize project.",
        )
        self.chief_of_staff.register_project(project)

        summary = self.chief_of_staff.project_summary("PROJ-0112")

        self.assertEqual(summary, project.summary())

    def _create_assigned_work_order(
        self,
        project_id,
        work_order_id,
        worker_id,
        project_status=ProjectStatus.PLANNED,
        priority=WorkOrderPriority.MEDIUM,
    ):
        project = self.chief_of_staff.create_project(
            project_id=project_id,
            title=f"Project {project_id}",
            client="JBK",
            description="Test project.",
            status=project_status,
        )
        worker = Executive(
            executive_id=worker_id,
            title="Chief Research Officer",
            mission="Own research outcomes.",
            status=ExecutiveStatus.AVAILABLE,
        )
        self.chief_of_staff.register_project(project)
        self.worker_registry.register(worker)
        work_order = self.chief_of_staff.create_work_order(
            project_id=project.id,
            work_order_id=work_order_id,
            title=f"WorkOrder {work_order_id}",
            objective="Test objective.",
            priority=priority,
        )
        self.chief_of_staff.assign_work_order(work_order.id, worker.id)
        return project, work_order, worker


if __name__ == "__main__":
    unittest.main()
