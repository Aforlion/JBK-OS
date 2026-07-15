import unittest

from core.deliverable import Deliverable, DeliverableStatus


class DeliverableTest(unittest.TestCase):
    def test_deliverable_can_be_instantiated(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0001",
            project_id="PROJ-0001",
            work_order_id="WO-0001",
            title="Research Report",
            author="EXEC-0001",
            content="Initial findings.",
        )

        self.assertEqual(deliverable.id, "DEL-0001")
        self.assertEqual(deliverable.project_id, "PROJ-0001")
        self.assertEqual(deliverable.work_order_id, "WO-0001")
        self.assertEqual(deliverable.title, "Research Report")
        self.assertEqual(deliverable.author, "EXEC-0001")
        self.assertEqual(deliverable.version, 1)
        self.assertEqual(deliverable.status, DeliverableStatus.DRAFT)
        self.assertEqual(deliverable.content, "Initial findings.")
        self.assertTrue(deliverable.created_at)
        self.assertTrue(deliverable.updated_at)

    def test_deliverable_receives_generated_id_when_not_supplied(self):
        deliverable = Deliverable(
            project_id="PROJ-0001",
            work_order_id="WO-0001",
            title="Generated ID",
            author="EXEC-0001",
        )

        self.assertRegex(deliverable.id, r"^DEL-\d{4}$")

    def test_id_is_immutable(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0002",
            project_id="PROJ-0002",
            work_order_id="WO-0002",
            title="Immutable ID",
            author="EXEC-0002",
        )

        with self.assertRaises(AttributeError):
            deliverable.id = "DEL-9999"

    def test_deliverable_references_business_objects_by_id_only(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0003",
            project_id="PROJ-0003",
            work_order_id="WO-0003",
            title="Reference Check",
            author="EXEC-0003",
        )

        self.assertEqual(deliverable.project_id, "PROJ-0003")
        self.assertEqual(deliverable.work_order_id, "WO-0003")
        self.assertEqual(deliverable.author, "EXEC-0003")
        self.assertFalse(hasattr(deliverable, "project"))
        self.assertFalse(hasattr(deliverable, "work_order"))
        self.assertFalse(hasattr(deliverable, "executive"))

    def test_version_starts_at_one_and_increments_correctly(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0004",
            project_id="PROJ-0004",
            work_order_id="WO-0004",
            title="Versioned Output",
            author="EXEC-0004",
        )

        next_version = deliverable.increment_version()

        self.assertEqual(next_version, 2)
        self.assertEqual(deliverable.version, 2)

    def test_content_updates_correctly(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0005",
            project_id="PROJ-0005",
            work_order_id="WO-0005",
            title="Content Update",
            author="EXEC-0005",
            content="Draft",
        )
        original_updated_at = deliverable.updated_at

        updated_content = deliverable.update_content("Final draft")

        self.assertEqual(updated_content, "Final draft")
        self.assertEqual(deliverable.content, "Final draft")
        self.assertNotEqual(deliverable.updated_at, original_updated_at)

    def test_status_transitions_work(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0006",
            project_id="PROJ-0006",
            work_order_id="WO-0006",
            title="Lifecycle Output",
            author="EXEC-0006",
        )

        self.assertEqual(deliverable.submit_for_review(), DeliverableStatus.IN_REVIEW)
        self.assertEqual(deliverable.status, DeliverableStatus.IN_REVIEW)

        self.assertEqual(deliverable.approve(), DeliverableStatus.APPROVED)
        self.assertEqual(deliverable.status, DeliverableStatus.APPROVED)

        self.assertEqual(deliverable.reject(), DeliverableStatus.REJECTED)
        self.assertEqual(deliverable.status, DeliverableStatus.REJECTED)

        self.assertEqual(deliverable.archive(), DeliverableStatus.ARCHIVED)
        self.assertEqual(deliverable.status, DeliverableStatus.ARCHIVED)

    def test_summary_returns_structured_data(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0007",
            project_id="PROJ-0007",
            work_order_id="WO-0007",
            title="Summary Output",
            author="EXEC-0007",
        )
        deliverable.submit_for_review()

        summary = deliverable.summary()

        self.assertEqual(
            summary,
            {
                "id": "DEL-0007",
                "project_id": "PROJ-0007",
                "work_order_id": "WO-0007",
                "title": "Summary Output",
                "author": "EXEC-0007",
                "version": 1,
                "status": "IN_REVIEW",
                "created_at": deliverable.created_at,
                "updated_at": deliverable.updated_at,
            },
        )

    def test_to_dict_returns_serializable_representation(self):
        deliverable = Deliverable(
            deliverable_id="DEL-0008",
            project_id="PROJ-0008",
            work_order_id="WO-0008",
            title="Serializable Output",
            author="EXEC-0008",
            content={"sections": ["overview", "recommendation"]},
        )

        deliverable_dict = deliverable.to_dict()

        self.assertEqual(
            deliverable_dict,
            {
                "id": "DEL-0008",
                "project_id": "PROJ-0008",
                "work_order_id": "WO-0008",
                "title": "Serializable Output",
                "author": "EXEC-0008",
                "version": 1,
                "status": "DRAFT",
                "content": {"sections": ["overview", "recommendation"]},
                "created_at": deliverable.created_at,
                "updated_at": deliverable.updated_at,
            },
        )

    def test_required_identity_fields_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "Project ID is required"):
            Deliverable(
                project_id="",
                work_order_id="WO-0009",
                title="Missing Project",
                author="EXEC-0009",
            )


if __name__ == "__main__":
    unittest.main()
