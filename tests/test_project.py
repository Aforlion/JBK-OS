import unittest

from core.project import Project, ProjectStatus


class ProjectTest(unittest.TestCase):
    def test_project_can_be_instantiated(self):
        project = Project(
            project_id="PROJ-0001",
            title="Operating System Build",
            client="JBK",
            description="Build the foundation of JBK Operating System.",
        )

        self.assertEqual(project.id, "PROJ-0001")
        self.assertEqual(project.title, "Operating System Build")
        self.assertEqual(project.client, "JBK")
        self.assertEqual(project.description, "Build the foundation of JBK Operating System.")
        self.assertEqual(project.status, ProjectStatus.PLANNED)
        self.assertEqual(project.work_orders, [])
        self.assertEqual(project.deliverables, [])
        self.assertEqual(project.decisions, [])
        self.assertTrue(project.created_at)
        self.assertTrue(project.updated_at)

    def test_project_receives_generated_id_when_not_supplied(self):
        project = Project(
            title="Research Initiative",
            client="JBK",
            description="Study customer workflows.",
        )

        self.assertRegex(project.id, r"^PROJ-\d{4}$")

    def test_work_orders_can_be_added(self):
        project = Project(
            project_id="PROJ-0002",
            title="Product Launch",
            client="JBK",
            description="Launch the first product release.",
        )
        work_order = {"id": "WO-0001", "title": "Draft launch plan"}

        added_work_order = project.add_work_order(work_order)

        self.assertEqual(added_work_order, work_order)
        self.assertEqual(project.work_orders, [work_order])

    def test_deliverables_can_be_added(self):
        project = Project(
            project_id="PROJ-0003",
            title="Executive Reporting",
            client="JBK",
            description="Create executive reporting outputs.",
        )
        deliverable = {"id": "DEL-0001", "title": "Weekly report"}

        added_deliverable = project.add_deliverable(deliverable)

        self.assertEqual(added_deliverable, deliverable)
        self.assertEqual(project.deliverables, [deliverable])

    def test_decisions_can_be_recorded(self):
        project = Project(
            project_id="PROJ-0004",
            title="Architecture Review",
            client="JBK",
            description="Review operating system architecture.",
        )
        decision = {"id": "DEC-0001", "summary": "Use standard library only."}

        recorded_decision = project.record_decision(decision)

        self.assertEqual(recorded_decision, decision)
        self.assertEqual(project.decisions, [decision])

    def test_status_changes_correctly_and_updates_timestamp(self):
        project = Project(
            project_id="PROJ-0005",
            title="Internal Initiative",
            client="JBK",
            description="Improve internal operations.",
        )
        original_updated_at = project.updated_at

        status = project.update_status(ProjectStatus.ACTIVE)

        self.assertEqual(status, ProjectStatus.ACTIVE)
        self.assertEqual(project.status, ProjectStatus.ACTIVE)
        self.assertNotEqual(project.updated_at, original_updated_at)

    def test_summary_returns_structured_data(self):
        project = Project(
            project_id="PROJ-0006",
            title="Research Program",
            client="JBK",
            description="Coordinate research activities.",
            status=ProjectStatus.ACTIVE,
        )
        project.add_work_order({"id": "WO-0002"})
        project.add_deliverable({"id": "DEL-0002"})
        project.record_decision({"id": "DEC-0002"})

        summary = project.summary()

        self.assertEqual(summary["id"], "PROJ-0006")
        self.assertEqual(summary["title"], "Research Program")
        self.assertEqual(summary["client"], "JBK")
        self.assertEqual(summary["status"], "ACTIVE")
        self.assertEqual(summary["work_order_count"], 1)
        self.assertEqual(summary["deliverable_count"], 1)
        self.assertEqual(summary["decision_count"], 1)
        self.assertTrue(summary["created_at"])
        self.assertTrue(summary["updated_at"])

    def test_to_dict_returns_serializable_representation(self):
        project = Project(
            project_id="PROJ-0007",
            title="Client Engagement",
            client="Example Client",
            description="Run a client engagement.",
        )
        work_order = {"id": "WO-0003"}
        deliverable = {"id": "DEL-0003"}
        decision = {"id": "DEC-0003"}
        project.add_work_order(work_order)
        project.add_deliverable(deliverable)
        project.record_decision(decision)

        project_dict = project.to_dict()

        self.assertEqual(
            project_dict,
            {
                "id": "PROJ-0007",
                "title": "Client Engagement",
                "client": "Example Client",
                "description": "Run a client engagement.",
                "status": "PLANNED",
                "work_orders": [work_order],
                "deliverables": [deliverable],
                "decisions": [decision],
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            },
        )

    def test_invalid_status_fails_clearly(self):
        project = Project(
            project_id="PROJ-0008",
            title="Compliance Project",
            client="JBK",
            description="Review compliance requirements.",
        )

        with self.assertRaisesRegex(ValueError, "Invalid project status"):
            project.update_status("UNKNOWN")

    def test_required_identity_fields_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "Project title is required"):
            Project(title="", client="JBK", description="Missing title.")


if __name__ == "__main__":
    unittest.main()
