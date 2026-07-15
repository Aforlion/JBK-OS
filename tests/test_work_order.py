import unittest

from core.work_order import WorkOrder, WorkOrderPriority, WorkOrderStatus


class WorkOrderTest(unittest.TestCase):
    def test_work_order_can_be_instantiated(self):
        work_order = WorkOrder(
            work_order_id="WO-0001",
            project_id="PROJ-0001",
            title="Implement WorkOrder",
            objective="Create the WorkOrder business object.",
        )

        self.assertEqual(work_order.id, "WO-0001")
        self.assertEqual(work_order.project_id, "PROJ-0001")
        self.assertEqual(work_order.title, "Implement WorkOrder")
        self.assertEqual(work_order.objective, "Create the WorkOrder business object.")
        self.assertIsNone(work_order.assigned_by)
        self.assertIsNone(work_order.assigned_to)
        self.assertEqual(work_order.priority, WorkOrderPriority.MEDIUM)
        self.assertEqual(work_order.status, WorkOrderStatus.CREATED)
        self.assertIsNone(work_order.deliverable_id)
        self.assertTrue(work_order.created_at)
        self.assertIsNone(work_order.assigned_at)
        self.assertIsNone(work_order.completed_at)
        self.assertTrue(work_order.updated_at)

    def test_work_order_receives_generated_id_when_not_supplied(self):
        work_order = WorkOrder(
            project_id="PROJ-0001",
            title="Generated ID",
            objective="Verify generated ID format.",
        )

        self.assertRegex(work_order.id, r"^WO-\d{4}$")

    def test_work_order_belongs_to_exactly_one_project_by_project_id(self):
        work_order = WorkOrder(
            work_order_id="WO-0002",
            project_id="PROJ-0002",
            title="Project Boundary",
            objective="Verify project reference.",
        )

        self.assertEqual(work_order.project_id, "PROJ-0002")
        self.assertFalse(hasattr(work_order, "project"))

    def test_status_transitions_work_correctly(self):
        work_order = WorkOrder(
            work_order_id="WO-0003",
            project_id="PROJ-0003",
            title="Lifecycle",
            objective="Verify lifecycle transitions.",
        )

        work_order.assign(assigned_by="EXEC-0001", assigned_to="EXEC-0002")
        self.assertEqual(work_order.status, WorkOrderStatus.ASSIGNED)
        self.assertEqual(work_order.assigned_by, "EXEC-0001")
        self.assertEqual(work_order.assigned_to, "EXEC-0002")
        self.assertTrue(work_order.assigned_at)

        work_order.accept()
        self.assertEqual(work_order.status, WorkOrderStatus.ACCEPTED)

        work_order.start()
        self.assertEqual(work_order.status, WorkOrderStatus.IN_PROGRESS)

        work_order.complete()
        self.assertEqual(work_order.status, WorkOrderStatus.COMPLETED)
        self.assertTrue(work_order.completed_at)

    def test_work_order_can_be_cancelled(self):
        work_order = WorkOrder(
            work_order_id="WO-0004",
            project_id="PROJ-0004",
            title="Cancellation",
            objective="Verify cancellation.",
        )

        work_order.cancel()

        self.assertEqual(work_order.status, WorkOrderStatus.CANCELLED)

    def test_priority_updates_correctly(self):
        work_order = WorkOrder(
            work_order_id="WO-0005",
            project_id="PROJ-0005",
            title="Priority",
            objective="Verify priority updates.",
            priority=WorkOrderPriority.LOW,
        )

        updated_priority = work_order.update_priority("CRITICAL")

        self.assertEqual(updated_priority, WorkOrderPriority.CRITICAL)
        self.assertEqual(work_order.priority, WorkOrderPriority.CRITICAL)

    def test_deliverable_id_can_be_attached(self):
        work_order = WorkOrder(
            work_order_id="WO-0006",
            project_id="PROJ-0006",
            title="Deliverable Reference",
            objective="Attach a deliverable ID.",
        )

        work_order.attach_deliverable("DEL-0001")

        self.assertEqual(work_order.deliverable_id, "DEL-0001")
        self.assertFalse(hasattr(work_order, "deliverable"))

    def test_summary_returns_structured_information(self):
        work_order = WorkOrder(
            work_order_id="WO-0007",
            project_id="PROJ-0007",
            title="Summary",
            objective="Verify summary output.",
            priority=WorkOrderPriority.HIGH,
        )
        work_order.assign(assigned_by="EXEC-0001", assigned_to="EXEC-0002")
        work_order.attach_deliverable("DEL-0002")

        summary = work_order.summary()

        self.assertEqual(
            summary,
            {
                "id": "WO-0007",
                "project_id": "PROJ-0007",
                "title": "Summary",
                "priority": "HIGH",
                "status": "ASSIGNED",
                "assigned_by": "EXEC-0001",
                "assigned_to": "EXEC-0002",
                "deliverable_id": "DEL-0002",
                "created_at": work_order.created_at,
                "updated_at": work_order.updated_at,
            },
        )

    def test_to_dict_returns_serializable_representation(self):
        work_order = WorkOrder(
            work_order_id="WO-0008",
            project_id="PROJ-0008",
            title="Serialization",
            objective="Verify dictionary output.",
            priority="HIGH",
        )
        work_order.assign(assigned_by="EXEC-0003", assigned_to="EXEC-0004")
        work_order.attach_deliverable("DEL-0003")

        work_order_dict = work_order.to_dict()

        self.assertEqual(
            work_order_dict,
            {
                "id": "WO-0008",
                "project_id": "PROJ-0008",
                "title": "Serialization",
                "objective": "Verify dictionary output.",
                "assigned_by": "EXEC-0003",
                "assigned_to": "EXEC-0004",
                "priority": "HIGH",
                "status": "ASSIGNED",
                "deliverable_id": "DEL-0003",
                "created_at": work_order.created_at,
                "assigned_at": work_order.assigned_at,
                "completed_at": work_order.completed_at,
                "updated_at": work_order.updated_at,
            },
        )

    def test_invalid_priority_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "Invalid work order priority"):
            WorkOrder(
                work_order_id="WO-0009",
                project_id="PROJ-0009",
                title="Invalid Priority",
                objective="Verify priority validation.",
                priority="URGENT",
            )

    def test_assignment_is_required_before_accepting(self):
        work_order = WorkOrder(
            work_order_id="WO-0010",
            project_id="PROJ-0010",
            title="Assignment Required",
            objective="Verify assignment guard.",
        )

        with self.assertRaisesRegex(ValueError, "assigned first"):
            work_order.accept()

    def test_required_identity_fields_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "Project ID is required"):
            WorkOrder(project_id="", title="Missing Project", objective="Missing project ID.")


if __name__ == "__main__":
    unittest.main()
