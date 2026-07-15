import unittest

from core.opportunity_brief import OpportunityBrief, OpportunityStatus
from core.opportunity_intake_engine import OpportunityIntakeEngine


class TestOpportunityIntake(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OpportunityIntakeEngine()

    def test_invalid_intake_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.intake(None)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.intake("")
        with self.assertRaises(ValueError):
            self.engine.intake("   ")

    def test_intake_technology_domain(self) -> None:
        req = "We need a new postgres database migrated to AWS. The timeline must be under 3 weeks. Contact: Alice (alice@jbk.com)."
        brief = self.engine.intake(req)
        self.assertEqual(brief.business_domain, "Technology")
        self.assertEqual(brief.status, OpportunityStatus.ANALYZED)
        self.assertEqual(brief.confidence_score, 0.8)  # Missing budget details (0.8 score)
        self.assertIn("What is your allocated budget for this initiative?", brief.recommended_next_questions)

    def test_intake_marketing_domain(self) -> None:
        req = "Our sales funnel is converting poorly. We aim to launch a new marketing campaign to increase conversion rates. Budget: $10,000. Target deadline: October 30. Contact: Bob."
        brief = self.engine.intake(req)
        self.assertEqual(brief.business_domain, "Marketing")
        self.assertEqual(brief.status, OpportunityStatus.ANALYZED)
        self.assertEqual(brief.confidence_score, 0.8)  # Missing tech stack details (0.8 score)

    def test_intake_operations_domain(self) -> None:
        req = "Our pipeline automation has a severe bottleneck. The current workflow is slow and inefficient. We want to optimize operations."
        brief = self.engine.intake(req)
        self.assertEqual(brief.business_domain, "Operations")
        # Missing budget, timeline, tech stack, and contact
        self.assertEqual(brief.status, OpportunityStatus.INSUFFICIENT_INFORMATION)
        self.assertEqual(brief.confidence_score, 0.2)
        self.assertEqual(brief.recommended_next_step, "Clarification Interview")

    def test_extract_problems_outcomes_and_constraints(self) -> None:
        req = "The current system is failing and slow. We want to implement a new database. It must run on Postgres."
        brief = self.engine.intake(req)
        self.assertEqual(brief.business_problems, ["The current system is failing and slow"])
        self.assertEqual(brief.desired_outcomes, ["We want to implement a new database"])
        self.assertEqual(brief.known_constraints, ["It must run on Postgres"])

    def test_brief_serialization(self) -> None:
        req = "Setup a server. Budget: $5k. Timeline: 2 days. Stack: Python. Contact: CEO."
        brief = self.engine.intake(req)
        
        sum_dict = brief.summary()
        self.assertEqual(sum_dict["opportunity_id"], brief.opportunity_id)
        self.assertEqual(sum_dict["business_domain"], "Technology")
        self.assertEqual(sum_dict["status"], "ANALYZED")
        
        to_dict_out = brief.to_dict()
        self.assertEqual(to_dict_out["opportunity_id"], brief.opportunity_id)
        self.assertEqual(to_dict_out["client_request_text"], req)
        self.assertEqual(to_dict_out["missing_information"], [])
        self.assertEqual(to_dict_out["recommended_next_questions"], [])
        self.assertEqual(to_dict_out["recommended_next_step"], "Generate Proposal")
