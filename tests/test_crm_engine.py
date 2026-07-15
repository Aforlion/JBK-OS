import unittest
from datetime import datetime, timezone, timedelta

from core.client_profile import ClientProfile
from core.client_interaction import ClientInteraction
from core.relationship_health import RelationshipHealth
from core.crm_report import CRMReport
from core.crm_engine import CRMEngine


class TestCRMEngine(unittest.TestCase):

    def test_client_registration_and_duplicate_prevention(self) -> None:
        engine = CRMEngine()
        
        # Success path
        profile = engine.register_client(
            company="Ministry of Education",
            industry="Education",
            organization_size=250,
            contact_people=["Jane Doe"],
            support_level="Premium",
            renewal_date="2027-01-01",
        )

        self.assertEqual(profile.company, "Ministry of Education")
        self.assertEqual(profile.industry, "Education")
        self.assertEqual(profile.organization_size, 250)
        self.assertEqual(profile.support_level, "Premium")
        self.assertTrue(profile.client_id.startswith("CLT-"))

        # Duplicate checking path (BR-042-001)
        with self.assertRaises(ValueError):
            engine.register_client(company="Ministry of Education")
            
        with self.assertRaises(ValueError):
            engine.register_client(company="  ministry of education  ")

    def test_interaction_logging_and_health_calculations(self) -> None:
        engine = CRMEngine()
        profile = engine.register_client(company="Client A")

        # Initial health defaults to Healthy (70 trust_score, 5 satisfaction)
        self.assertEqual(profile.relationship_status, RelationshipHealth.STATUS_HEALTHY)

        # Log routine meeting
        meeting = engine.log_interaction(
            client_id=profile.client_id,
            interaction_type="meeting",
            description="Discuss project scope",
            outcome="Successful alignment",
        )
        self.assertEqual(meeting.interaction_type, "meeting")
        self.assertEqual(profile.relationship_status, RelationshipHealth.STATUS_HEALTHY)

        # Log complaint (Satisfaction drops to 4, health drops to Watch due to complaint)
        engine.log_interaction(
            client_id=profile.client_id,
            interaction_type="complaint",
            description="Late delivery of layout mockup",
            outcome="Unresolved",
        )
        self.assertEqual(profile.satisfaction_score, 4.0)
        self.assertEqual(profile.relationship_status, RelationshipHealth.STATUS_WATCH)

    def test_trust_score_adjustments_on_project_status(self) -> None:
        engine = CRMEngine()
        profile = engine.register_client(company="Client B")
        profile.active_projects.append("PROJ-0001")

        # Project completion (BR-042-007: Completed projects increase trust score)
        engine.process_project_completion(profile.client_id, "PROJ-0001", success=True)
        self.assertEqual(profile.trust_score, 75.0)
        self.assertNotIn("PROJ-0001", profile.active_projects)
        self.assertIn("PROJ-0001", profile.past_projects)

        # Project failure (BR-042-008: Failed projects decrease trust score)
        profile.active_projects.append("PROJ-0002")
        engine.process_project_completion(profile.client_id, "PROJ-0002", success=False)
        self.assertEqual(profile.trust_score, 60.0)

    def test_strategic_account_detection(self) -> None:
        engine = CRMEngine()
        profile = engine.register_client(company="Big Org", organization_size=600)
        self.assertTrue(engine.is_strategic_account(profile.client_id))

        profile2 = engine.register_client(company="Rich Org")
        profile2.lifetime_value = 150000.0
        self.assertTrue(engine.is_strategic_account(profile2.client_id))

        profile3 = engine.register_client(company="Small Org", organization_size=50)
        self.assertFalse(engine.is_strategic_account(profile3.client_id))

    def test_renewal_predictions_and_recommendation_generation(self) -> None:
        engine = CRMEngine()
        profile = engine.register_client(
            company="Client C",
            renewal_date=(datetime.now(timezone.utc) + timedelta(days=45)).strftime("%Y-%m-%d")
        )

        # Generate report
        report = engine.generate_report(profile.client_id)
        self.assertEqual(len(report.upcoming_renewals), 1)
        self.assertEqual(report.upcoming_renewals[0]["probability"], "High")

        # Advisory recommendations check
        self.assertTrue(any("Routine outreach" in r for r in report.recommended_actions))

        # Check cold client risk
        profile.renewal_date = None
        # Simulate long-ago interaction
        cold_time = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        engine.log_interaction(
            client_id=profile.client_id,
            interaction_type="meeting",
            description="Old meeting",
            timestamp=cold_time
        )
        cold_report = engine.generate_report(profile.client_id)
        self.assertTrue(any("Client going cold" in r for r in cold_report.risks))

    def test_serialization(self) -> None:
        profile = ClientProfile(client_id="CLT-0001", company="Test Company")
        d = profile.to_dict()
        self.assertEqual(d["client_id"], "CLT-0001")
        self.assertEqual(d["company"], "Test Company")

        interaction = ClientInteraction(
            interaction_id="INT-0001",
            client_id="CLT-0001",
            interaction_type="email",
            description="Quick check",
        )
        idict = interaction.to_dict()
        self.assertEqual(idict["interaction_id"], "INT-0001")
        self.assertEqual(idict["interaction_type"], "email")


if __name__ == "__main__":
    unittest.main()
