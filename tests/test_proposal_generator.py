import unittest
from datetime import datetime, timezone

from core.commercial_proposal import CommercialProposal
from core.client_proposal import ClientProposal
from core.proposal_generator import ProposalGenerator


class TestProposalGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = ProposalGenerator()
        
        self.comm_proposal = CommercialProposal(
            proposal_id="PRP-0001",
            estimate_id="EST-0001",
            client_summary="Client summary text",
            project_summary="Project summary text",
            commercial_strategy="Value-Based",
            conservative_price=15000.0,
            recommended_price=20000.0,
            premium_price=30000.0,
            expected_gross_margin=50.0,
            pricing_rationale="Rationale",
            commercial_risks=[{"risk": "Scope Creep", "mitigation": "Mitigation"}],
            payment_structure="50/50 Split",
            payment_milestones=[],
            maintenance_recommendation="Maintenance",
            support_recommendation="Support",
            warranty_recommendation="Warranty",
            licensing_recommendation="Licensing",
            optional_services=[{"service": "Training", "price": 2500.0, "billing_cycle": "One-time"}],
            commercial_assumptions=["Assumption"],
            negotiation_notes={"discount_guidance": "Discount", "non_negotiables": []},
            executive_recommendation="Executive Recommendation",
            confidence_score=0.9,
        )

    def test_invalid_generate_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.generator.generate_proposal(None, "Client", "Org")  # type: ignore

    def test_generate_proposal_success(self) -> None:
        proposal = self.generator.generate_proposal(self.comm_proposal, "Alice Smith", "Acme Corp")
        self.assertIsInstance(proposal, ClientProposal)
        self.assertEqual(proposal.proposal_id, "PRP-0001")
        self.assertEqual(proposal.proposal_version, "1.0")
        self.assertEqual(proposal.client_name, "Alice Smith")
        self.assertEqual(proposal.client_organization, "Acme Corp")
        self.assertEqual(proposal.commercial_investment, 20000.0)
        self.assertEqual(proposal.payment_terms, "50/50 Split")
        self.assertEqual(len(proposal.optional_services), 1)
        self.assertEqual(proposal.optional_services[0]["service"], "Training")
        
        # Verify confidentiality: dict serialization does NOT contain cost/margin/conf/negotiation variables
        data = proposal.to_dict()
        self.assertNotIn("cost_basis", data)
        self.assertNotIn("expected_gross_margin", data)
        self.assertNotIn("confidence_score", data)
        self.assertNotIn("negotiation_notes", data)
        self.assertNotIn("conservative_price", data)
        self.assertNotIn("premium_price", data)

    def test_rendering_outputs(self) -> None:
        proposal = self.generator.generate_proposal(self.comm_proposal, "Bob", "Initech")
        
        # Test Markdown
        md = proposal.render_markdown()
        self.assertIn("# Professional Services Proposal - Initech", md)
        self.assertIn("## Executive Summary", md)
        self.assertIn("**Total Professional Fee:** $20,000.00", md)
        self.assertIn("Accepted By:", md)
        
        # Test Text
        text = proposal.render_text()
        self.assertNotIn("# ", text)
        self.assertNotIn("## ", text)
        self.assertIn("Total Professional Fee: $20,000.00", text)

    def test_serialization(self) -> None:
        proposal = self.generator.generate_proposal(self.comm_proposal, "Charlie", "Cyberdyne")
        summary = proposal.summary()
        self.assertEqual(summary["proposal_id"], "PRP-0001")
        self.assertEqual(summary["commercial_investment"], 20000.0)
