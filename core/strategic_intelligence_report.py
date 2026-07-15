from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class StrategicInsight:
    def __init__(self, insight_id: str, title: str, description: str, source: str) -> None:
        if not insight_id:
            raise ValueError("Insight ID is required.")
        if not title:
            raise ValueError("Title is required.")
            
        self.insight_id = insight_id
        self.title = title
        self.description = description
        self.source = source

    def summary(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "source": self.source,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
        }


class MarketOpportunity(StrategicInsight):
    def __init__(
        self,
        insight_id: str,
        title: str,
        description: str,
        source: str,
        market_segment: str,
        estimated_size: str,
    ) -> None:
        super().__init__(insight_id, title, description, source)
        self.market_segment = market_segment
        self.estimated_size = estimated_size

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "type": "MarketOpportunity",
            "market_segment": self.market_segment,
            "estimated_size": self.estimated_size,
        })
        return d


class CompetitiveThreat(StrategicInsight):
    def __init__(
        self,
        insight_id: str,
        title: str,
        description: str,
        source: str,
        competitor_name: str,
        threat_level: str,
    ) -> None:
        super().__init__(insight_id, title, description, source)
        self.competitor_name = competitor_name
        self.threat_level = threat_level

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "type": "CompetitiveThreat",
            "competitor_name": self.competitor_name,
            "threat_level": self.threat_level,
        })
        return d


class TechnologyTrend(StrategicInsight):
    def __init__(
        self,
        insight_id: str,
        title: str,
        description: str,
        source: str,
        technology_area: str,
        maturity_level: str,
    ) -> None:
        super().__init__(insight_id, title, description, source)
        self.technology_area = technology_area
        self.maturity_level = maturity_level

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "type": "TechnologyTrend",
            "technology_area": self.technology_area,
            "maturity_level": self.maturity_level,
        })
        return d


class StrategicRecommendation:
    ALLOWED_IMPACTS = {"Low", "Medium", "High", "Transformational"}
    ALLOWED_CATEGORIES = {
        "Technology", "Market", "Competition", "Regulation",
        "Product", "Operations", "Partnership", "Investment"
    }

    def __init__(
        self,
        recommendation_id: str,
        title: str,
        description: str,
        category: str,
        confidence_level: float,
        expected_business_impact: str,
        supporting_evidence: list[str],
        recommended_action: str,
    ) -> None:
        if not recommendation_id:
            raise ValueError("Recommendation ID is required.")
        if expected_business_impact not in self.ALLOWED_IMPACTS:
            raise ValueError(f"Invalid impact: {expected_business_impact}. Allowed: {self.ALLOWED_IMPACTS}")
        if category not in self.ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Allowed: {self.ALLOWED_CATEGORIES}")
        if not supporting_evidence:
            raise ValueError("Every recommendation must cite supporting intelligence (evidence).")

        self.recommendation_id = recommendation_id
        self.title = title
        self.description = description
        self.category = category
        self.confidence_level = max(0.0, min(1.0, confidence_level))
        self.expected_business_impact = expected_business_impact
        self.supporting_evidence = list(supporting_evidence)
        self.recommended_action = recommended_action

    def summary(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "category": self.category,
            "expected_business_impact": self.expected_business_impact,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "confidence_level": self.confidence_level,
            "expected_business_impact": self.expected_business_impact,
            "supporting_evidence": list(self.supporting_evidence),
            "recommended_action": self.recommended_action,
        }


class StrategicIntelligenceReport:
    def __init__(
        self,
        report_id: str,
        emerging_opportunities: list[MarketOpportunity],
        emerging_risks: list[StrategicInsight],
        technology_watch: list[TechnologyTrend],
        industry_trends: list[StrategicInsight],
        competitive_analysis: list[CompetitiveThreat],
        client_opportunity_signals: list[MarketOpportunity],
        strategic_recommendations: list[StrategicRecommendation],
        ceo_action_items: list[StrategicRecommendation],
        created_at: str | None = None,
    ) -> None:
        if not report_id:
            raise ValueError("Report ID is required.")

        self.report_id = report_id
        self.emerging_opportunities = list(emerging_opportunities or [])
        self.emerging_risks = list(emerging_risks or [])
        self.technology_watch = list(technology_watch or [])
        self.industry_trends = list(industry_trends or [])
        self.competitive_analysis = list(competitive_analysis or [])
        self.client_opportunity_signals = list(client_opportunity_signals or [])
        self.strategic_recommendations = list(strategic_recommendations or [])
        self.ceo_action_items = list(ceo_action_items or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "opportunity_count": len(self.emerging_opportunities) + len(self.client_opportunity_signals),
            "risk_count": len(self.emerging_risks),
            "technology_trend_count": len(self.technology_watch),
            "competitive_threat_count": len(self.competitive_analysis),
            "recommendation_count": len(self.strategic_recommendations),
            "ceo_action_item_count": len(self.ceo_action_items),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "emerging_opportunities": [item.to_dict() for item in self.emerging_opportunities],
            "emerging_risks": [item.to_dict() for item in self.emerging_risks],
            "technology_watch": [item.to_dict() for item in self.technology_watch],
            "industry_trends": [item.to_dict() for item in self.industry_trends],
            "competitive_analysis": [item.to_dict() for item in self.competitive_analysis],
            "client_opportunity_signals": [item.to_dict() for item in self.client_opportunity_signals],
            "strategic_recommendations": [item.to_dict() for item in self.strategic_recommendations],
            "ceo_action_items": [item.to_dict() for item in self.ceo_action_items],
            "created_at": self.created_at,
        }
