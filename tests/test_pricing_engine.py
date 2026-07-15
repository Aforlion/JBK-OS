import unittest

from core.project_estimate import ProjectEstimate
from core.commercial_proposal import CommercialProposal
from core.pricing_engine import PricingEngine


class TestPricingEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PricingEngine()
        
        self.est_small = ProjectEstimate(
            estimate_id="EST-0001",
            blueprint_id="BLP-0001",
            client_summary="Small request",
            solution_summary="Small solution",
            delivery_complexity="Low",
            estimated_duration="2 weeks",
            estimated_effort="80 hours",
            best_case_duration=1.5,
            expected_duration=2.0,
            worst_case_duration=3.0,
            best_case_effort=60.0,
            expected_effort=80.0,
            worst_case_effort=120.0,
            required_departments=["Technology"],
            required_executive_roles=["Chief of Staff"],
            required_skills=["software-engineer"],
            required_capabilities=["API Integration"],
            resource_requirements={},
            delivery_strategy="Kanban",
            major_milestones=[],
            critical_dependencies=[],
            risk_buffer={},
            key_assumptions=[],
            known_constraints=[],
            confidence_score=0.8,
            executive_notes="",
        )

        self.est_large = ProjectEstimate(
            estimate_id="EST-0002",
            blueprint_id="BLP-0002",
            client_summary="Enterprise request",
            solution_summary="Enterprise solution",
            delivery_complexity="Enterprise",
            estimated_duration="24 weeks",
            estimated_effort="960 hours",
            best_case_duration=18.0,
            expected_duration=24.0,
            worst_case_duration=36.0,
            best_case_effort=720.0,
            expected_effort=960.0,
            worst_case_effort=1440.0,
            required_departments=["Technology", "Operations"],
            required_executive_roles=["Chief of Staff", "Startup CTO"],
            required_skills=["software-engineer", "process-optimizer"],
            required_capabilities=["API Integration", "AI Automation"],
            resource_requirements={},
            delivery_strategy="Waterfall",
            major_milestones=[],
            critical_dependencies=[],
            risk_buffer={},
            key_assumptions=[],
            known_constraints=[],
            confidence_score=1.0,
            executive_notes="",
        )

    def test_invalid_pricing_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.price_project(None)  # type: ignore

    def test_price_small_project(self) -> None:
        proposal = self.engine.price_project(self.est_small)
        self.assertIsInstance(proposal, CommercialProposal)
        
        # Math verification
        # Cost basis = 80 hours * $150 = $12,000
        # Recommended = $12,000 * 2 = $24,000
        # Expected gross margin = (24000 - 12000)/24000 = 50%
        self.assertEqual(proposal.recommended_price, 24000.0)
        self.assertEqual(proposal.conservative_price, 18000.0)  # 12000 * 1.5
        self.assertEqual(proposal.expected_gross_margin, 50.0)
        
        # Payment Split: Low complexity -> 50/50 Split
        self.assertIn("50/50 Split", proposal.payment_structure)
        self.assertEqual(proposal.payment_milestones[0]["amount"], 12000.0)

    def test_price_large_project(self) -> None:
        proposal = self.engine.price_project(self.est_large)
        self.assertEqual(proposal.commercial_strategy, "Strategic Partnership Pricing")
        
        # Math verification
        # Cost basis = 960 hours * $150 = $144,000
        # Recommended = $144,000 * 2 = $288,000
        self.assertEqual(proposal.recommended_price, 288000.0)
        
        # Payment Split: Enterprise complexity -> 20/20/30/30 Split
        self.assertIn("Milestone Payments", proposal.payment_structure)
        self.assertEqual(proposal.payment_milestones[0]["percentage"], 20.0)
        self.assertEqual(proposal.payment_milestones[0]["amount"], 57600.0) # 288000 * 0.2

    def test_negotiation_guidance_and_risks(self) -> None:
        proposal = self.engine.price_project(self.est_small)
        self.assertIn("Scope Creep", [r["risk"] for r in proposal.commercial_risks])
        self.assertIn("IP rights remain JBK property until final invoice is cleared.", proposal.negotiation_notes["non_negotiables"])

    def test_serialization(self) -> None:
        proposal = self.engine.price_project(self.est_small)
        summary = proposal.summary()
        self.assertEqual(summary["proposal_id"], proposal.proposal_id)
        self.assertEqual(summary["recommended_price"], 24000.0)
        
        to_dict_out = proposal.to_dict()
        self.assertEqual(to_dict_out["proposal_id"], proposal.proposal_id)
        self.assertEqual(to_dict_out["estimate_id"], "EST-0001")
        self.assertEqual(len(to_dict_out["payment_milestones"]), 2)
