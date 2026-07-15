import unittest

from core.discovery_plan import DiscoveryPlan
from core.solution_blueprint import SolutionBlueprint
from core.solution_architect import SolutionArchitect


class TestSolutionArchitect(unittest.TestCase):
    def setUp(self) -> None:
        self.architect = SolutionArchitect()
        self.plan_empty = DiscoveryPlan(
            discovery_id="DSC-0001",
            opportunity_id="OPP-0001",
            conversation_objective="None",
            information_already_known=[],
            information_still_required=[],
            recommended_question_sequence=[],
            conversation_categories=[],
            discovery_completeness=0.0,
            confidence_score=0.2,
            recommended_next_step="Discovery",
        )
        self.plan_complete = DiscoveryPlan(
            discovery_id="DSC-0002",
            opportunity_id="OPP-0002",
            conversation_objective="Deploy scalable server",
            information_already_known=[
                "Business Domain: Technology",
                "Problem: System runs slow and crashes",
                "Outcome Goal: Increase system speed",
                "Constraint: Budget limit is $15k"
            ],
            information_still_required=[],
            recommended_question_sequence=[],
            conversation_categories=[],
            discovery_completeness=1.0,
            confidence_score=1.0,
            recommended_next_step="Scope Solution",
        )

    def test_invalid_design_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.architect.design_solution(None)  # type: ignore

    def test_design_solution_empty_plan(self) -> None:
        blueprint = self.architect.design_solution(self.plan_empty)
        self.assertIsInstance(blueprint, SolutionBlueprint)
        self.assertEqual(blueprint.confidence_score, 0.1)  # completeness=0.0 -> score = 0.0*0.9+0.1 = 0.1
        self.assertEqual(blueprint.business_problem, "Unspecified business pain points.")

    def test_design_solution_complete_plan(self) -> None:
        blueprint = self.architect.design_solution(self.plan_complete)
        self.assertEqual(blueprint.confidence_score, 1.0)  # completeness=1.0 -> score = 1.0*0.9+0.1 = 1.0
        self.assertIn("System runs slow and crashes", blueprint.business_problem)
        
        # Verify Root Cause Analysis Symptoms and Root Causes
        rca = blueprint.root_cause_analysis
        self.assertIn("System runs slow and crashes", rca["symptoms"])
        self.assertIn("Outdated process orchestration or legacy pipelines", rca["root_problems"])
        self.assertEqual(rca["business_constraints"], ["Budget limit is $15k"])
        
        # Verify capabilities
        self.assertIn("Web Development", blueprint.required_capabilities)
        self.assertIn("AI Automation", blueprint.required_capabilities)
        self.assertIn("software-engineer", blueprint.required_skills)
        self.assertEqual(blueprint.required_departments, ["Technology", "Operations"])

    def test_serialization(self) -> None:
        blueprint = self.architect.design_solution(self.plan_complete)
        summary = blueprint.summary()
        self.assertEqual(summary["blueprint_id"], blueprint.blueprint_id)
        self.assertEqual(summary["confidence_score"], 1.0)
        
        to_dict_out = blueprint.to_dict()
        self.assertEqual(to_dict_out["blueprint_id"], blueprint.blueprint_id)
        self.assertEqual(to_dict_out["discovery_plan_id"], "DSC-0002")
        self.assertEqual(len(to_dict_out["proposed_solution_options"]), 2)
        self.assertIsNotNone(to_dict_out["recommended_solution"])
