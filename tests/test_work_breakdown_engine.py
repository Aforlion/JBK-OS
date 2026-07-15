import unittest

from core.delivery_plan import DeliveryPlan
from core.work_breakdown_structure import WorkBreakdownStructure
from core.work_breakdown_engine import WorkBreakdownEngine


class TestWorkBreakdownEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = WorkBreakdownEngine()
        
        self.plan_low = DeliveryPlan(
            delivery_plan_id="DPL-0001",
            project_id="PROJ-0001",
            phases=[
                {
                    "title": "Design & Implementation",
                    "description": "Consolidated setup",
                    "duration_weeks": 2.0,
                    "priority": "HIGH",
                    "milestones": ["MVP Completed"]
                },
                {
                    "title": "Deployment & Handoff",
                    "description": "Production rollout",
                    "duration_weeks": 1.0,
                    "priority": "MEDIUM",
                    "milestones": ["Project Closure"]
                }
            ],
            work_streams=[
                {
                    "title": "Technology Work Stream",
                    "required_capabilities": ["Web Development", "API Integration"]
                },
                {
                    "title": "Operations Work Stream",
                    "required_capabilities": ["Training"]
                }
            ],
            dependencies=[]
        )

    def test_invalid_breakdown_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.generate_wbs(None)  # type: ignore

    def test_generate_wbs_success(self) -> None:
        wbs = self.engine.generate_wbs(self.plan_low)
        self.assertIsInstance(wbs, WorkBreakdownStructure)
        self.assertEqual(wbs.project_id, "PROJ-0001")
        self.assertEqual(wbs.delivery_plan_id, "DPL-0001")
        
        # 2 phases * 2 streams = 4 tasks total
        self.assertEqual(len(wbs.tasks), 4)
        
        # Check hierarchy preservation
        first_task = wbs.tasks[0]
        self.assertEqual(first_task["task_id"], "TSK-01-01")
        self.assertEqual(first_task["phase_title"], "Design & Implementation")
        self.assertEqual(first_task["work_stream_title"], "Technology Work Stream")
        
        # Check capabilities extraction
        self.assertIn("Web Development", first_task["recommended_capabilities"])
        
        # Check effort calculation
        # Tech stream: 2.0 weeks * 20.0 effort + 10.0 integration = 50.0 hours
        self.assertEqual(first_task["estimated_effort_hours"], 50.0)
        
        # Check advisory dependencies (Phase 2 tasks should depend on Phase 1 tasks TSK-01-01 and TSK-01-02)
        phase2_task = wbs.tasks[2] # TSK-02-01
        self.assertEqual(phase2_task["task_id"], "TSK-02-01")
        self.assertIn("TSK-01-01", phase2_task["dependencies"])
        self.assertIn("TSK-01-02", phase2_task["dependencies"])

    def test_serialization(self) -> None:
        wbs = self.engine.generate_wbs(self.plan_low)
        summary = wbs.summary()
        self.assertEqual(summary["wbs_id"], wbs.wbs_id)
        self.assertEqual(summary["task_count"], 4)
        
        to_dict_out = wbs.to_dict()
        self.assertEqual(to_dict_out["wbs_id"], wbs.wbs_id)
        self.assertEqual(to_dict_out["delivery_plan_id"], "DPL-0001")
        self.assertEqual(len(to_dict_out["tasks"]), 4)
