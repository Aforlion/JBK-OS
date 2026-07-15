import unittest

from core.work_breakdown_structure import WorkBreakdownStructure
from core.worker_registry import WorkerRegistry
from core.skill_registry import SkillRegistry
from core.executive import Executive
from core.skill import Skill
from core.resource_allocation_plan import ResourceAllocationPlan
from core.resource_allocation_engine import ResourceAllocationEngine


class TestResourceAllocationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ResourceAllocationEngine()
        self.worker_registry = WorkerRegistry()
        self.skill_registry = SkillRegistry()

        # Set up workers
        self.worker_tech = Executive(
            executive_id="EXEC-0001",
            title="Senior Developer",
            mission="Write high quality code",
        )
        self.worker_ops = Executive(
            executive_id="EXEC-0002",
            title="Operations Manager",
            mission="Coordinate workflows",
        )
        
        self.worker_registry.register(self.worker_tech)
        self.worker_registry.register(self.worker_ops)

        # Set up skills owned by workers to map capabilities
        self.skill_tech = Skill(
            skill_id="SKL-0001",
            name="Coding Skill",
            description="Write software integrations",
            owner_id="EXEC-0001",
            department="Technology",
            execution_engine="Python",
            capabilities=["Web Development", "API Integration"],
            inputs=[],
            outputs=[],
            version="1.0"
        )
        self.skill_ops = Skill(
            skill_id="SKL-0002",
            name="Workflow Skill",
            description="Manage processes",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Manual",
            capabilities=["Training", "Documentation"],
            inputs=[],
            outputs=[],
            version="1.0"
        )

        self.skill_registry.register(self.skill_tech)
        self.skill_registry.register(self.skill_ops)

        # Create WorkBreakdownStructure
        self.wbs = WorkBreakdownStructure(
            wbs_id="WBS-0001",
            project_id="PROJ-0001",
            delivery_plan_id="DPL-0001",
            tasks=[
                {
                    "task_id": "TSK-01",
                    "title": "Backend Setup",
                    "estimated_effort_hours": 30.0,
                    "recommended_capabilities": ["API Integration"]
                },
                {
                    "task_id": "TSK-02",
                    "title": "Staff Training",
                    "estimated_effort_hours": 15.0,
                    "recommended_capabilities": ["Training"]
                },
                {
                    "task_id": "TSK-03",
                    "title": "Security Check",
                    "estimated_effort_hours": 10.0,
                    "recommended_capabilities": ["Security Review"] # No available worker owns this (will be unassigned)
                },
                {
                    "task_id": "TSK-04",
                    "title": "Database Connect",
                    "estimated_effort_hours": 20.0,
                    "recommended_capabilities": ["API Integration"] # Should overload EXEC-0001 (30 + 20 = 50 > 40)
                }
            ]
        )

    def test_invalid_allocation_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.allocate_resources(None, self.worker_registry, self.skill_registry)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.allocate_resources(self.wbs, None, self.skill_registry)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.allocate_resources(self.wbs, self.worker_registry, None)  # type: ignore

    def test_allocate_resources_success(self) -> None:
        plan = self.engine.allocate_resources(self.wbs, self.worker_registry, self.skill_registry)
        self.assertIsInstance(plan, ResourceAllocationPlan)
        self.assertEqual(plan.project_id, "PROJ-0001")
        
        # Verify assignments: TSK-01 assigned to EXEC-0001, TSK-02 to EXEC-0002
        assigned_ids = {a["task_id"]: a["worker_id"] for a in plan.assignments}
        self.assertEqual(assigned_ids["TSK-01"], "EXEC-0001")
        self.assertEqual(assigned_ids["TSK-02"], "EXEC-0002")
        self.assertEqual(assigned_ids["TSK-04"], "EXEC-0001")
        
        # Verify unassigned tasks
        unassigned_ids = [t["task_id"] for t in plan.unassigned_tasks]
        self.assertIn("TSK-03", unassigned_ids)
        
        # Check warnings
        self.assertTrue(any("overloaded" in w for w in plan.warnings))
        self.assertTrue(any("unassigned" in w for w in plan.warnings))

    def test_serialization(self) -> None:
        plan = self.engine.allocate_resources(self.wbs, self.worker_registry, self.skill_registry)
        summary = plan.summary()
        self.assertEqual(summary["allocation_id"], plan.allocation_id)
        self.assertEqual(summary["assigned_task_count"], 3)
        self.assertEqual(summary["unassigned_task_count"], 1)
        
        to_dict_out = plan.to_dict()
        self.assertEqual(to_dict_out["allocation_id"], plan.allocation_id)
        self.assertEqual(len(to_dict_out["assignments"]), 3)
