import unittest

from core.project import Project, ProjectStatus
from core.project_registry import ProjectRegistry


class ProjectRegistryTest(unittest.TestCase):
    def test_project_registry_can_be_instantiated(self):
        registry = ProjectRegistry()

        self.assertEqual(registry.list_projects(), [])

    def test_projects_can_be_registered(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0001",
            title="Operating System Build",
            client="JBK",
            description="Build the operating system foundation.",
        )

        registered_project = registry.register(project)

        self.assertIs(registered_project, project)
        self.assertEqual(registry.list_projects(), [project])

    def test_duplicate_project_ids_are_rejected(self):
        registry = ProjectRegistry()
        first_project = Project(
            project_id="PROJ-0002",
            title="Research Program",
            client="JBK",
            description="Coordinate research work.",
        )
        second_project = Project(
            project_id="PROJ-0002",
            title="Product Program",
            client="JBK",
            description="Coordinate product work.",
        )
        registry.register(first_project)

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(second_project)

    def test_projects_can_be_removed(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0003",
            title="Client Engagement",
            client="Example Client",
            description="Run a client engagement.",
        )
        registry.register(project)

        removed_project = registry.unregister("PROJ-0003")

        self.assertIs(removed_project, project)
        self.assertEqual(registry.list_projects(), [])
        self.assertIsNone(registry.find_by_id("PROJ-0003"))

    def test_unregister_removes_only_registry_reference(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0004",
            title="Internal Initiative",
            client="JBK",
            description="Improve internal operations.",
            status=ProjectStatus.ACTIVE,
        )
        registry.register(project)

        removed_project = registry.unregister("PROJ-0004")

        self.assertIs(removed_project, project)
        self.assertEqual(project.id, "PROJ-0004")
        self.assertEqual(project.status, ProjectStatus.ACTIVE)

    def test_projects_can_be_found_by_id(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0005",
            title="Architecture Review",
            client="JBK",
            description="Review technical architecture.",
        )
        registry.register(project)

        found_project = registry.find_by_id("PROJ-0005")

        self.assertIs(found_project, project)

    def test_projects_can_be_listed(self):
        registry = ProjectRegistry()
        first_project = Project(
            project_id="PROJ-0006",
            title="First Project",
            client="JBK",
            description="First project.",
        )
        second_project = Project(
            project_id="PROJ-0007",
            title="Second Project",
            client="JBK",
            description="Second project.",
        )
        registry.register(first_project)
        registry.register(second_project)

        self.assertEqual(registry.list_projects(), [first_project, second_project])

    def test_projects_can_be_filtered_by_status(self):
        registry = ProjectRegistry()
        active_project = Project(
            project_id="PROJ-0008",
            title="Active Project",
            client="JBK",
            description="Active work.",
            status=ProjectStatus.ACTIVE,
        )
        completed_project = Project(
            project_id="PROJ-0009",
            title="Completed Project",
            client="JBK",
            description="Completed work.",
            status=ProjectStatus.COMPLETED,
        )
        registry.register(active_project)
        registry.register(completed_project)

        active_projects = registry.list_by_status(ProjectStatus.ACTIVE)
        completed_projects = registry.list_by_status("COMPLETED")

        self.assertEqual(active_projects, [active_project])
        self.assertEqual(completed_projects, [completed_project])

    def test_registry_does_not_modify_project_state(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0010",
            title="State Check",
            client="JBK",
            description="Ensure registry does not mutate projects.",
            status=ProjectStatus.ON_HOLD,
        )
        original_updated_at = project.updated_at

        registry.register(project)
        registry.list_by_status(ProjectStatus.ON_HOLD)
        registry.unregister("PROJ-0010")

        self.assertEqual(project.status, ProjectStatus.ON_HOLD)
        self.assertEqual(project.updated_at, original_updated_at)

    def test_summary_returns_structured_information(self):
        registry = ProjectRegistry()
        active_project = Project(
            project_id="PROJ-0011",
            title="Active Project",
            client="JBK",
            description="Active project.",
            status=ProjectStatus.ACTIVE,
        )
        completed_project = Project(
            project_id="PROJ-0012",
            title="Completed Project",
            client="JBK",
            description="Completed project.",
            status=ProjectStatus.COMPLETED,
        )
        on_hold_project = Project(
            project_id="PROJ-0013",
            title="On Hold Project",
            client="JBK",
            description="Paused project.",
            status=ProjectStatus.ON_HOLD,
        )
        planned_project = Project(
            project_id="PROJ-0014",
            title="Planned Project",
            client="JBK",
            description="Planned project.",
            status=ProjectStatus.PLANNED,
        )
        registry.register(active_project)
        registry.register(completed_project)
        registry.register(on_hold_project)
        registry.register(planned_project)

        summary = registry.summary()

        self.assertEqual(
            summary,
            {
                "total_projects": 4,
                "projects_by_status": {
                    "ACTIVE": 1,
                    "COMPLETED": 1,
                    "ON_HOLD": 1,
                    "PLANNED": 1,
                },
                "active_projects": 1,
                "completed_projects": 1,
                "on_hold_projects": 1,
            },
        )

    def test_to_dict_returns_serializable_representation(self):
        registry = ProjectRegistry()
        project = Project(
            project_id="PROJ-0015",
            title="Serializable Project",
            client="JBK",
            description="Verify registry serialization.",
        )
        registry.register(project)

        registry_dict = registry.to_dict()

        self.assertEqual(registry_dict["projects"], [project.to_dict()])
        self.assertEqual(registry_dict["summary"]["total_projects"], 1)

    def test_register_requires_project_id(self):
        registry = ProjectRegistry()

        with self.assertRaisesRegex(ValueError, "Project must have an ID"):
            registry.register(object())


if __name__ == "__main__":
    unittest.main()
