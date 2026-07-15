import unittest

from core.executive import Executive, ExecutiveStatus


class ExecutiveTest(unittest.TestCase):
    def test_executive_can_be_instantiated(self):
        executive = Executive(
            executive_id="EXEC-0001",
            title="Chief of Staff",
            mission="Coordinate executive work.",
        )

        self.assertEqual(executive.id, "EXEC-0001")
        self.assertEqual(executive.title, "Chief of Staff")
        self.assertEqual(executive.mission, "Coordinate executive work.")
        self.assertEqual(executive.status, ExecutiveStatus.AVAILABLE)
        self.assertEqual(executive.assigned_work_orders, [])
        self.assertEqual(executive.completed_work_orders, [])
        self.assertTrue(executive.created_at)
        self.assertTrue(executive.updated_at)

    def test_executive_can_receive_work_order(self):
        executive = Executive(
            executive_id="EXEC-0002",
            title="Chief Research Officer",
            mission="Own research outcomes.",
        )
        work_order = {"id": "WO-0001", "title": "Prepare research brief"}

        received_work_order = executive.receive_work_order(work_order)

        self.assertEqual(received_work_order, work_order)
        self.assertIn(work_order, executive.assigned_work_orders)

    def test_executive_can_accept_assigned_work_order(self):
        executive = Executive(
            executive_id="EXEC-0003",
            title="Chief Product Officer",
            mission="Own product outcomes.",
        )
        work_order = {"id": "WO-0002", "title": "Review roadmap"}
        executive.receive_work_order(work_order)

        accepted_work_order = executive.accept_work_order(work_order)

        self.assertEqual(accepted_work_order, work_order)
        self.assertEqual(executive.status, ExecutiveStatus.BUSY)

    def test_executive_can_mark_work_order_complete(self):
        executive = Executive(
            executive_id="EXEC-0004",
            title="Chief Technology Officer",
            mission="Own technology outcomes.",
        )
        work_order = {"id": "WO-0003", "title": "Assess architecture"}
        executive.receive_work_order(work_order)
        executive.accept_work_order(work_order)

        completed_work_order = executive.complete_work_order(work_order)

        self.assertEqual(completed_work_order, work_order)
        self.assertNotIn(work_order, executive.assigned_work_orders)
        self.assertIn(work_order, executive.completed_work_orders)
        self.assertEqual(executive.status, ExecutiveStatus.AVAILABLE)

    def test_executive_can_submit_deliverable_for_completed_work_order(self):
        executive = Executive(
            executive_id="EXEC-0005",
            title="Chief Finance Officer",
            mission="Own finance outcomes.",
        )
        work_order = {"id": "WO-0004", "title": "Prepare budget review"}
        deliverable = {"id": "DEL-0001", "title": "Budget review"}
        executive.receive_work_order(work_order)
        executive.complete_work_order(work_order)

        submission = executive.submit_deliverable(work_order, deliverable)

        self.assertEqual(submission["executive_id"], "EXEC-0005")
        self.assertEqual(submission["work_order"], work_order)
        self.assertEqual(submission["deliverable"], deliverable)
        self.assertTrue(submission["submitted_at"])

    def test_executive_generates_structured_report(self):
        executive = Executive(
            executive_id="EXEC-0006",
            title="Chief Operating Officer",
            mission="Own operating outcomes.",
        )
        assigned_work_order = {"id": "WO-0005", "title": "Review operating plan"}
        completed_work_order = {"id": "WO-0006", "title": "Publish weekly update"}
        executive.receive_work_order(assigned_work_order)
        executive.receive_work_order(completed_work_order)
        executive.complete_work_order(completed_work_order)

        report = executive.generate_report()

        self.assertEqual(report["executive"]["id"], "EXEC-0006")
        self.assertEqual(report["executive"]["assigned_work_orders"], [assigned_work_order])
        self.assertEqual(report["executive"]["completed_work_orders"], [completed_work_order])
        self.assertEqual(
            report["summary"],
            {
                "assigned_work_order_count": 1,
                "completed_work_order_count": 1,
                "status": "BUSY",
            },
        )

    def test_invalid_status_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "Invalid executive status"):
            Executive(
                executive_id="EXEC-0007",
                title="Chief Legal Officer",
                mission="Own legal outcomes.",
                status="UNKNOWN",
            )

    def test_unassigned_work_order_cannot_be_completed(self):
        executive = Executive(
            executive_id="EXEC-0008",
            title="Chief Customer Officer",
            mission="Own customer outcomes.",
        )

        with self.assertRaisesRegex(ValueError, "not assigned"):
            executive.complete_work_order({"id": "WO-0007"})


if __name__ == "__main__":
    unittest.main()
