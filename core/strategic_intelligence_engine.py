import logging
from typing import Any

from core.organizational_knowledge import OrganizationalKnowledge
from core.portfolio_report import PortfolioReport
from core.strategic_intelligence_report import (
    StrategicInsight,
    MarketOpportunity,
    CompetitiveThreat,
    TechnologyTrend,
    StrategicRecommendation,
    StrategicIntelligenceReport,
)

LOGGER = logging.getLogger(__name__)


class StrategicIntelligenceEngine:
    """Advisory engine that transforms external information into executive intelligence."""

    def __init__(self) -> None:
        self._report_counter = 1
        self._insight_counter = 1
        self._recommendation_counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_intelligence_report(
        self,
        organizational_knowledge: list[OrganizationalKnowledge] | None = None,
        portfolio_reports: list[PortfolioReport] | None = None,
        industry_research: list[dict[str, Any]] | None = None,
        market_research: list[dict[str, Any]] | None = None,
        competitor_intelligence: list[dict[str, Any]] | None = None,
        technology_intelligence: list[dict[str, Any]] | None = None,
        regulatory_intelligence: list[dict[str, Any]] | None = None,
        client_feedback: list[dict[str, Any]] | None = None,
        executive_notes: list[dict[str, Any]] | None = None,
    ) -> StrategicIntelligenceReport:
        report_id = self._next_report_id()
        LOGGER.info("object_id=%s action=generate_intelligence_report actor=system status=DRAFT", report_id)

        # Parse inputs into internal normalized lists
        organizational_knowledge = organizational_knowledge or []
        portfolio_reports = portfolio_reports or []
        industry_research = industry_research or []
        market_research = market_research or []
        competitor_intelligence = competitor_intelligence or []
        technology_intelligence = technology_intelligence or []
        regulatory_intelligence = regulatory_intelligence or []
        client_feedback = client_feedback or []
        executive_notes = executive_notes or []

        # Combine all generic dict sources for initial processing
        raw_insights: list[dict[str, Any]] = []
        raw_insights.extend(self._normalize_input(industry_research, "Industry Research"))
        raw_insights.extend(self._normalize_input(market_research, "Market Research"))
        raw_insights.extend(self._normalize_input(competitor_intelligence, "Competitor Intelligence"))
        raw_insights.extend(self._normalize_input(technology_intelligence, "Technology Intelligence"))
        raw_insights.extend(self._normalize_input(regulatory_intelligence, "Regulatory Intelligence"))
        raw_insights.extend(self._normalize_input(client_feedback, "Client Feedback"))
        raw_insights.extend(self._normalize_input(executive_notes, "Executive Notes"))

        # Deduplicate
        unique_raw_insights = self._deduplicate_raw_insights(raw_insights)

        # Initialize categorised lists
        emerging_opportunities: list[MarketOpportunity] = []
        emerging_risks: list[StrategicInsight] = []
        technology_watch: list[TechnologyTrend] = []
        industry_trends: list[StrategicInsight] = []
        competitive_analysis: list[CompetitiveThreat] = []
        client_opportunity_signals: list[MarketOpportunity] = []

        # Categorize unique raw insights into strongly typed models
        for raw in unique_raw_insights:
            insight = self._categorize_insight(raw)
            if isinstance(insight, TechnologyTrend):
                technology_watch.append(insight)
            elif isinstance(insight, CompetitiveThreat):
                competitive_analysis.append(insight)
            elif isinstance(insight, MarketOpportunity):
                if raw["source"] == "Client Feedback":
                    client_opportunity_signals.append(insight)
                else:
                    emerging_opportunities.append(insight)
            else:
                if "risk" in raw.get("title", "").lower() or "threat" in raw.get("title", "").lower():
                    emerging_risks.append(insight)
                else:
                    industry_trends.append(insight)

        # Extract intelligence from Org Knowledge and Portfolio Reports
        self._extract_knowledge_opportunities(organizational_knowledge, emerging_opportunities)
        self._extract_portfolio_trends(portfolio_reports, industry_trends)

        # Generate Strategic Recommendations based on parsed insights
        all_insights = (
            emerging_opportunities + emerging_risks + technology_watch +
            industry_trends + competitive_analysis + client_opportunity_signals
        )
        
        strategic_recommendations = self._derive_recommendations(all_insights)

        # Promote high impact/high confidence recommendations to CEO action items
        ceo_action_items = [
            rec for rec in strategic_recommendations
            if rec.expected_business_impact in ("High", "Transformational") and rec.confidence_level >= 0.8
        ]

        LOGGER.info(
            "object_id=%s action=generate_intelligence_report actor=system status=READY insights=%d recommendations=%d", 
            report_id, len(all_insights), len(strategic_recommendations)
        )

        return StrategicIntelligenceReport(
            report_id=report_id,
            emerging_opportunities=emerging_opportunities,
            emerging_risks=emerging_risks,
            technology_watch=technology_watch,
            industry_trends=industry_trends,
            competitive_analysis=competitive_analysis,
            client_opportunity_signals=client_opportunity_signals,
            strategic_recommendations=strategic_recommendations,
            ceo_action_items=ceo_action_items,
        )

    # ------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------

    def _normalize_input(self, data: list[dict[str, Any]], default_source: str) -> list[dict[str, Any]]:
        normalized = []
        for item in data:
            normalized.append({
                "title": item.get("title", "Untitled Insight"),
                "description": item.get("description", ""),
                "source": item.get("source", default_source),
                "category": item.get("category", ""),
                "competitor_name": item.get("competitor_name", ""),
                "technology_area": item.get("technology_area", ""),
                "market_segment": item.get("market_segment", ""),
            })
        return normalized

    def _deduplicate_raw_insights(self, raw_insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate insights based on title or description exact/substring matches."""
        unique_insights: list[dict[str, Any]] = []
        seen_titles = set()

        for insight in raw_insights:
            title_lower = insight["title"].lower().strip()
            
            # Simple keyword deduplication based on exact title match
            if title_lower in seen_titles:
                continue

            # Alternatively, skip if the title is a substring of an existing title
            is_duplicate = False
            for seen in seen_titles:
                if title_lower in seen or seen in title_lower:
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue

            seen_titles.add(title_lower)
            unique_insights.append(insight)

        return unique_insights

    def _categorize_insight(self, raw: dict[str, Any]) -> StrategicInsight:
        iid = self._next_insight_id()
        source = raw["source"]
        title = raw["title"]
        desc = raw["description"]

        if source == "Competitor Intelligence" or raw.get("competitor_name"):
            return CompetitiveThreat(
                insight_id=iid,
                title=title,
                description=desc,
                source=source,
                competitor_name=raw.get("competitor_name", "Unknown Competitor"),
                threat_level="High" if "disrupt" in desc.lower() else "Medium",
            )
            
        if source == "Technology Intelligence" or raw.get("technology_area"):
            return TechnologyTrend(
                insight_id=iid,
                title=title,
                description=desc,
                source=source,
                technology_area=raw.get("technology_area", "Emerging Tech"),
                maturity_level="Early Stage" if "alpha" in desc.lower() else "Maturing",
            )
            
        if source in ("Market Research", "Client Feedback") or raw.get("market_segment"):
            return MarketOpportunity(
                insight_id=iid,
                title=title,
                description=desc,
                source=source,
                market_segment=raw.get("market_segment", "General Market"),
                estimated_size="Unknown",
            )

        return StrategicInsight(
            insight_id=iid,
            title=title,
            description=desc,
            source=source,
        )

    def _extract_knowledge_opportunities(
        self,
        knowledge_list: list[OrganizationalKnowledge],
        emerging_opportunities: list[MarketOpportunity],
    ) -> None:
        for ok in knowledge_list:
            if hasattr(ok, "future_recommendations") and ok.future_recommendations:
                for rec in ok.future_recommendations:
                    if "opportunity" in rec.lower() or "market" in rec.lower():
                        emerging_opportunities.append(
                            MarketOpportunity(
                                insight_id=self._next_insight_id(),
                                title=f"Knowledge Base Insight: {rec[:30]}...",
                                description=rec,
                                source="Organizational Knowledge",
                                market_segment="Internal Discovery",
                                estimated_size="TBD",
                            )
                        )

    def _extract_portfolio_trends(
        self,
        portfolio_reports: list[PortfolioReport],
        industry_trends: list[StrategicInsight],
    ) -> None:
        for report in portfolio_reports:
            for opp in getattr(report, "strategic_opportunities", []):
                industry_trends.append(
                    StrategicInsight(
                        insight_id=self._next_insight_id(),
                        title="Portfolio Trend Observation",
                        description=str(opp),
                        source="Portfolio Reports",
                    )
                )

    def _derive_recommendations(self, insights: list[StrategicInsight]) -> list[StrategicRecommendation]:
        recs: list[StrategicRecommendation] = []
        
        for insight in insights:
            # We generate a recommendation for highly actionable insights
            impact = "Medium"
            category = "Market"
            confidence = 0.6
            action = "Monitor situation and report next quarter."
            
            if isinstance(insight, CompetitiveThreat):
                category = "Competition"
                impact = "High" if insight.threat_level == "High" else "Medium"
                confidence = 0.8
                action = f"Initiate competitive counter-strategy analysis against {insight.competitor_name}."
            
            elif isinstance(insight, TechnologyTrend):
                category = "Technology"
                if "AI" in insight.title or "LLM" in insight.title:
                    impact = "Transformational"
                    confidence = 0.9
                    action = "Establish internal working group to evaluate technology adoption."
                else:
                    impact = "Medium"
            
            elif isinstance(insight, MarketOpportunity):
                category = "Market"
                if insight.source == "Client Feedback":
                    impact = "High"
                    action = "Develop rapid MVP to test market appetite with existing client base."
                    confidence = 0.85
                else:
                    impact = "Medium"
                    action = "Commission deeper market sizing report."

            # Map "Regulation"
            if "regulat" in insight.title.lower() or "law" in insight.title.lower():
                category = "Regulation"
                impact = "High"
                action = "Engage legal counsel to assess compliance requirements."

            # Only generate recommendations for insights that appear significant
            if impact in ("High", "Transformational"):
                recs.append(
                    StrategicRecommendation(
                        recommendation_id=self._next_recommendation_id(),
                        title=f"Action required regarding: {insight.title}",
                        description=f"Based on {insight.source}, action is required to address {insight.title}.",
                        category=category,
                        confidence_level=confidence,
                        expected_business_impact=impact,
                        supporting_evidence=[insight.insight_id, insight.source],
                        recommended_action=action,
                    )
                )

        return recs

    # ------------------------------------------------------------------
    # ID Generators
    # ------------------------------------------------------------------

    def _next_report_id(self) -> str:
        rid = f"SIR-{self._report_counter:04d}"
        self._report_counter += 1
        return rid

    def _next_insight_id(self) -> str:
        iid = f"INS-{self._insight_counter:04d}"
        self._insight_counter += 1
        return iid

    def _next_recommendation_id(self) -> str:
        rid = f"SREC-{self._recommendation_counter:04d}"
        self._recommendation_counter += 1
        return rid
