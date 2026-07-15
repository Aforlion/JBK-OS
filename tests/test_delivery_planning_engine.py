import unittest

from core.delivery_plan import DeliveryPlan
from core.delivery_planning_engine import DeliveryPlanningEngine


class TestDeliveryPlanningEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DeliveryPlanningEngine()
        self.details_low = {
            "title": "Small Project",
            "complexity": "Low",
            "domain": "Operations",
        }
        self.details_high = {
            "title": "Enterprise Integration",
            "complexity": "Enterprise",
            "domain": "Technology",
        }

    def test_invalid_planning_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.generate_delivery_plan("", self.details_low)
        with self.assertRaises(ValueError):
            self.engine.generate_delivery_plan("PROJ-0001", None)  # type: ignore

    def test_low_complexity_plan(self) -> None:
        plan = self.engine.generate_delivery_plan("PROJ-0001", self.details_low)
        self.assertIsInstance(plan, DeliveryPlan)
        self.assertEqual(plan.project_id, "PROJ-0001")
        
        # Verify 2 phases for Low complexity
        self.assertEqual(len(plan.phases), 2)
        phase_titles = [p["title"] for p in plan.phases]
        self.assertIn("Design & Implementation", phase_titles)
        self.assertIn("Deployment & Handoff", phase_titles)
        
        # Verify 2 streams (Technology, Operations)
        self.assertEqual(len(plan.work_streams), 2)
        
        # Verify dependencies (Deployment depends on Implementation)
        self.assertEqual(len(plan.dependencies), 1)
        self.assertEqual(plan.dependencies[0]["task"], "Deployment & Handoff")
        self.assertEqual(plan.dependencies[0]["depends_on"], "Design & Implementation")

    def test_high_complexity_plan(self) -> None:
        plan = self.engine.generate_delivery_plan("PROJ-0002", self.details_high)
        
        # Verify 4 phases for high/enterprise complexity
        self.assertEqual(len(plan.phases), 4)
        
        # Verify 3 work streams (Tech, Ops, Compliance)
        self.assertEqual(len(plan.work_streams), 3)
        stream_titles = [s["title"] for s in plan.work_streams]
        self.assertIn("Compliance Work Stream", stream_titles)
        
        # Verify capabilities matching titles
        for s in plan.work_streams:
            if "compliance" in s["title"].lower():
                self.assertIn("Security Review", s["required_capabilities"])
            elif "technology" in s["title"].lower():
                self.assertIn("API Integration", s["required_capabilities"])
                
        # Milestones check
        milestones = self.engine.generate_milestones(self.details_high)
        self.assertIn("Discovery Complete", milestones)
        self.assertIn("Architecture Approved", milestones)

    def test_serialization(self) -> None:
        plan = self.engine.generate_delivery_plan("PROJ-0001", self.details_low)
        summary = plan.summary()
        self.assertEqual(summary["delivery_plan_id"], plan.delivery_plan_id)
        self.assertEqual(summary["phase_count"], 2)
        
        to_dict_out = plan.to_dict()
        self.assertEqual(to_dict_out["delivery_plan_id"], plan.delivery_plan_id)
        self.assertEqual(to_dict_out["project_id"], "PROJ-0001")
        self.assertEqual(len(to_dict_out["phases"]), 2)
