import unittest
from typing import Any

from core.organizational_knowledge import OrganizationalKnowledge
from core.strategic_intelligence_report import (
    StrategicInsight,
    MarketOpportunity,
    CompetitiveThreat,
    TechnologyTrend,
    StrategicRecommendation,
    StrategicIntelligenceReport,
)
from core.strategic_intelligence_engine import StrategicIntelligenceEngine


class MockPortfolioReport:
    def __init__(self, strategic_opportunities: list[str]) -> None:
        self.strategic_opportunities = strategic_opportunities


class TestStrategicIntelligenceEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = StrategicIntelligenceEngine()

    # ------------------------------------------------------------------
    # Input Validation & Boundary
    # ------------------------------------------------------------------

    def test_advisory_boundaries_respected(self) -> None:
        org_knowledge = [OrganizationalKnowledge(
            knowledge_id="KN-1",
            title="General Tech Knowledge",
            category="GENERAL",
            source_project_ids=["P-1"],
            future_recommendations=["Explore market opportunity in EdTech"],
        )]
        
        # Count items before
        ok_count = len(org_knowledge)
        
        report = self.engine.generate_intelligence_report(
            organizational_knowledge=org_knowledge
        )
        
        # Asserts no mutation
        self.assertEqual(len(org_knowledge), ok_count)
        self.assertIsInstance(report, StrategicIntelligenceReport)

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    def test_deduplicates_exact_titles(self) -> None:
        industry_research = [
            {"title": "AI in Healthcare"},
            {"title": "ai in healthcare "},  # Should deduplicate
            {"title": "Blockchain in Finance"},
        ]
        
        report = self.engine.generate_intelligence_report(industry_research=industry_research)
        
        # We expect 2 unique insights, both categorized as industry_trends (default if not risk/opp/tech/comp)
        # But wait, one of them has 'AI' so it might become a tech trend? Let's check total counts.
        total_insights = sum([
            len(report.emerging_opportunities),
            len(report.emerging_risks),
            len(report.technology_watch),
            len(report.industry_trends),
            len(report.competitive_analysis),
            len(report.client_opportunity_signals),
        ])
        
        self.assertEqual(total_insights, 2)

    def test_deduplicates_substring_titles(self) -> None:
        competitor_intel = [
            {"title": "Competitor X launches new feature"},
            {"title": "Competitor X launches new feature today"},
        ]
        report = self.engine.generate_intelligence_report(competitor_intelligence=competitor_intel)
        self.assertEqual(len(report.competitive_analysis), 1)

    # ------------------------------------------------------------------
    # Categorization & Evidence
    # ------------------------------------------------------------------

    def test_categorizes_technology_watch(self) -> None:
        tech_intel = [
            {"title": "New LLM Framework", "description": "An alpha version of a new LLM."}
        ]
        report = self.engine.generate_intelligence_report(technology_intelligence=tech_intel)
        
        self.assertEqual(len(report.technology_watch), 1)
        tech_trend = report.technology_watch[0]
        self.assertIsInstance(tech_trend, TechnologyTrend)
        self.assertEqual(tech_trend.maturity_level, "Early Stage")  # From 'alpha' in desc

    def test_categorizes_competitive_threat(self) -> None:
        comp_intel = [
            {"title": "Rival Corp Expansion", "description": "They will disrupt our market."}
        ]
        report = self.engine.generate_intelligence_report(competitor_intelligence=comp_intel)
        
        self.assertEqual(len(report.competitive_analysis), 1)
        comp = report.competitive_analysis[0]
        self.assertIsInstance(comp, CompetitiveThreat)
        self.assertEqual(comp.threat_level, "High")  # From 'disrupt' in desc

    def test_extracts_knowledge_opportunities(self) -> None:
        org_knowledge = [OrganizationalKnowledge(
            knowledge_id="KN-1",
            title="General Tech Knowledge",
            category="GENERAL",
            source_project_ids=["P-1"],
            future_recommendations=["Opportunity to build an enterprise tier."],
        )]
        report = self.engine.generate_intelligence_report(organizational_knowledge=org_knowledge)
        
        self.assertEqual(len(report.emerging_opportunities), 1)
        self.assertIn("Knowledge Base Insight", report.emerging_opportunities[0].title)

    def test_extracts_portfolio_trends(self) -> None:
        portfolio = [MockPortfolioReport(["Expand to EU market."])]
        report = self.engine.generate_intelligence_report(portfolio_reports=portfolio) # type: ignore
        self.assertEqual(len(report.industry_trends), 1)

    # ------------------------------------------------------------------
    # Recommendation Generation & Validation
    # ------------------------------------------------------------------

    def test_generates_recommendation_with_evidence(self) -> None:
        tech_intel = [{"title": "Revolutionary AI tool", "description": "Game changer."}]
        report = self.engine.generate_intelligence_report(technology_intelligence=tech_intel)
        
        # 'AI' triggers Transformational impact and recommendation
        self.assertGreater(len(report.strategic_recommendations), 0)
        rec = report.strategic_recommendations[0]
        
        self.assertEqual(rec.expected_business_impact, "Transformational")
        self.assertGreater(len(rec.supporting_evidence), 0)
        self.assertEqual(rec.category, "Technology")

    def test_ceo_escalation(self) -> None:
        tech_intel = [{"title": "New AI product", "description": "Huge."}]
        report = self.engine.generate_intelligence_report(technology_intelligence=tech_intel)
        
        # AI creates a Transformational impact with 0.9 confidence -> Should be in CEO Action items
        self.assertGreater(len(report.ceo_action_items), 0)

    def test_recommendation_object_validation(self) -> None:
        with self.assertRaises(ValueError):
            StrategicRecommendation(
                recommendation_id="R-1",
                title="T",
                description="D",
                category="Technology",
                confidence_level=0.5,
                expected_business_impact="InvalidImpact",  # Raises
                supporting_evidence=["E1"],
                recommended_action="Act",
            )
            
        with self.assertRaises(ValueError):
            StrategicRecommendation(
                recommendation_id="R-1",
                title="T",
                description="D",
                category="InvalidCategory", # Raises
                confidence_level=0.5,
                expected_business_impact="High",
                supporting_evidence=["E1"],
                recommended_action="Act",
            )
            
        with self.assertRaises(ValueError):
            StrategicRecommendation(
                recommendation_id="R-1",
                title="T",
                description="D",
                category="Technology",
                confidence_level=0.5,
                expected_business_impact="High",
                supporting_evidence=[],  # Raises empty evidence
                recommended_action="Act",
            )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_report_serialization(self) -> None:
        tech_intel = [{"title": "New AI product", "description": "Huge."}]
        report = self.engine.generate_intelligence_report(technology_intelligence=tech_intel)
        
        d = report.to_dict()
        self.assertIn("report_id", d)
        self.assertIn("technology_watch", d)
        self.assertIn("strategic_recommendations", d)
        self.assertIn("ceo_action_items", d)
        self.assertEqual(len(d["technology_watch"]), 1)
        
    def test_summary_structure(self) -> None:
        tech_intel = [{"title": "New AI product", "description": "Huge."}]
        report = self.engine.generate_intelligence_report(technology_intelligence=tech_intel)
        
        s = report.summary()
        self.assertIn("technology_trend_count", s)
        self.assertEqual(s["technology_trend_count"], 1)

    def test_report_id_format(self) -> None:
        report = self.engine.generate_intelligence_report()
        self.assertTrue(report.report_id.startswith("SIR-"))


if __name__ == "__main__":
    unittest.main()
