import unittest

from core.opportunity_brief import OpportunityBrief, OpportunityStatus
from core.discovery_plan import DiscoveryPlan
from core.discovery_conversation_engine import DiscoveryConversationEngine


class TestDiscoveryConversation(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DiscoveryConversationEngine()
        self.brief_empty = OpportunityBrief(
            opportunity_id="OPP-0001",
            client_request_text="Setup a server.",
            business_domain="Technology",
            business_problems=[],
            desired_outcomes=[],
            known_constraints=[],
            missing_information=["Budget missing.", "Timeline missing.", "Technology missing.", "Contact missing."],
            recommended_next_questions=[],
            complexity_rating="Low",
            confidence_score=0.2,
            recommended_next_step="Clarification",
        )
        self.brief_complete = OpportunityBrief(
            opportunity_id="OPP-0002",
            client_request_text="Setup server. Budget is $10k. Timeline: 2 weeks. Tech: Python.",
            business_domain="Technology",
            business_problems=["Current runs slow"],
            desired_outcomes=["Faster server"],
            known_constraints=["Must use Python", "Budget is $10k"],
            missing_information=[],
            recommended_next_questions=[],
            complexity_rating="Low",
            confidence_score=1.0,
            recommended_next_step="Scoping",
        )

    def test_invalid_generate_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.generate_plan(None)  # type: ignore

    def test_generate_plan_empty_brief(self) -> None:
        plan = self.engine.generate_plan(self.brief_empty)
        self.assertIsInstance(plan, DiscoveryPlan)
        self.assertEqual(plan.discovery_completeness, 0.0)
        self.assertEqual(plan.recommended_next_step, "Discovery Call")
        
        # Verify 11 categories exist
        self.assertEqual(len(plan.conversation_categories), 11)
        self.assertIn("Business", plan.conversation_categories)
        self.assertIn("Risks", plan.conversation_categories)

    def test_prioritization_and_avoid_redundancy(self) -> None:
        plan = self.engine.generate_plan(self.brief_complete)
        self.assertEqual(plan.discovery_completeness, 1.0)
        self.assertEqual(plan.recommended_next_step, "Scope Solution")
        
        # Check questions: 'Budget' should be skipped because it is already known in constraints
        q_categories = [q["category"] for q in plan.recommended_question_sequence]
        self.assertNotIn("Budget", q_categories)
        
        # Verify priority sorting (first element should have priority 1, last element 3 or 2)
        self.assertEqual(plan.recommended_question_sequence[0]["priority"], 1)
        self.assertGreaterEqual(plan.recommended_question_sequence[-1]["priority"], 1)

    def test_serialization(self) -> None:
        plan = self.engine.generate_plan(self.brief_empty)
        summary = plan.summary()
        self.assertEqual(summary["discovery_id"], plan.discovery_id)
        self.assertEqual(summary["discovery_completeness"], 0.0)
        
        to_dict_out = plan.to_dict()
        self.assertEqual(to_dict_out["discovery_id"], plan.discovery_id)
        self.assertEqual(to_dict_out["opportunity_id"], "OPP-0001")
        self.assertEqual(len(to_dict_out["conversation_categories"]), 11)
