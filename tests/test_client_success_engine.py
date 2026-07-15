import unittest
from datetime import datetime, timezone, timedelta

from core.client_profile import ClientProfile
from core.crm_report import CRMReport
from core.knowledge_registry import KnowledgeRegistry
from core.client_success_engine import ClientSuccessEngine


class TestClientSuccessEngine(unittest.TestCase):

    def test_customer_lifecycle_and_scheduling(self) -> None:
        engine = ClientSuccessEngine()
        registry = KnowledgeRegistry()

        # Onboarding state: has active project, no past projects
        profile_onboarding = ClientProfile(
            client_id="CLT-0001",
            company="New Client",
            active_projects=["PROJ-0001"],
            past_projects=[],
            trust_score=70.0,
            satisfaction_score=4.0,
        )

        report = engine.evaluate_success(profile_onboarding, knowledge_registry=registry)
        self.assertEqual(report.status, "ONBOARDING")
        self.assertEqual(report.support_schedule.frequency, "Weekly")
        self.assertEqual(report.relationship_trend, "Stable")

        # Advocate state: past projects, high satisfaction, high trust
        profile_advocate = ClientProfile(
            client_id="CLT-0002",
            company="Happy Client",
            active_projects=[],
            past_projects=["PROJ-0001"],
            trust_score=95.0,
            satisfaction_score=5.0,
        )

        report_adv = engine.evaluate_success(profile_advocate, knowledge_registry=registry)
        self.assertEqual(report_adv.status, "ADVOCATE")
        self.assertEqual(report_adv.support_schedule.frequency, "Annual")
        self.assertEqual(report_adv.relationship_trend, "Improving")

    def test_renewal_and_upsell_detection(self) -> None:
        engine = ClientSuccessEngine()
        registry = KnowledgeRegistry()

        profile = ClientProfile(
            client_id="CLT-0003",
            company="Strategic Client",
            renewal_date="2027-06-30",
            lifetime_value=120000.0,
            past_projects=["PROJ-0001"],
        )

        report = engine.evaluate_success(profile, knowledge_registry=registry)
        
        # Renewal Opportunity check
        self.assertEqual(len(report.renewal_opportunities), 1)
        renewal = report.renewal_opportunities[0]
        self.assertEqual(renewal.renewal_type, "Support contract renewal")
        self.assertEqual(renewal.confidence, "High")
        self.assertEqual(renewal.estimated_value, 24000.0)

        # Upsell check
        self.assertTrue(any(u.upsell_type == "AI Automation Upgrade" for u in report.upsell_opportunities))

    def test_risk_alerts_and_recommendations(self) -> None:
        engine = ClientSuccessEngine()
        registry = KnowledgeRegistry()

        # At risk profile
        profile = ClientProfile(
            client_id="CLT-0004",
            company="Critical Corp",
            relationship_status="Critical",
            satisfaction_score=2.0,
            trust_score=40.0,
        )

        crm_rep = CRMReport(
            report_id="REP-0001",
            client_id="CLT-0004",
            relationship_score=40.0,
            risks=["Late payment issues", "Complaint filed"],
        )

        report = engine.evaluate_success(profile, crm_report=crm_rep, knowledge_registry=registry)
        self.assertEqual(report.status, "AT_RISK")
        self.assertTrue(any(r.risk_type == "declining health" for r in report.risk_alerts))
        self.assertTrue(any("Executive Visit" in rec for rec in report.executive_recommendations))

    def test_advisory_boundary(self) -> None:
        # Verify that evaluating success does not mutate or modify client profile/CRM values
        engine = ClientSuccessEngine()
        profile = ClientProfile(
            client_id="CLT-0005",
            company="Immutable Client",
            trust_score=70.0,
            satisfaction_score=4.0,
        )
        
        orig_trust = profile.trust_score
        orig_sat = profile.satisfaction_score
        orig_company = profile.company

        engine.evaluate_success(profile)
        
        self.assertEqual(profile.trust_score, orig_trust)
        self.assertEqual(profile.satisfaction_score, orig_sat)
        self.assertEqual(profile.company, orig_company)

    def test_knowledge_capture(self) -> None:
        engine = ClientSuccessEngine()
        registry = KnowledgeRegistry()
        profile = ClientProfile(client_id="CLT-0006", company="Knowledge Corp")

        engine.evaluate_success(profile, knowledge_registry=registry)
        
        # Check if success strategy knowledge was captured
        items = registry.list_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Success Strategy: Knowledge Corp")
        self.assertEqual(items[0].category, "Client Success")


if __name__ == "__main__":
    unittest.main()
