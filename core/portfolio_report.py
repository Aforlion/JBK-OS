from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class PortfolioMetrics:
    def __init__(
        self,
        total_active_projects: int,
        portfolio_health_score: float,
        average_delivery_health: float,
        resource_utilization_percent: float,
        projects_by_industry: dict[str, int],
        projects_by_status: dict[str, int],
        critical_project_count: int,
        capacity_remaining: int,
        knowledge_assets_generated: int,
        average_client_satisfaction: float | None = None,
    ) -> None:
        self.total_active_projects = max(0, total_active_projects)
        self.portfolio_health_score = max(0.0, min(1.0, portfolio_health_score))
        self.average_delivery_health = max(0.0, min(1.0, average_delivery_health))
        self.resource_utilization_percent = max(0.0, min(100.0, resource_utilization_percent))
        self.projects_by_industry = dict(projects_by_industry or {})
        self.projects_by_status = dict(projects_by_status or {})
        self.critical_project_count = max(0, critical_project_count)
        self.capacity_remaining = capacity_remaining
        self.knowledge_assets_generated = max(0, knowledge_assets_generated)
        self.average_client_satisfaction = average_client_satisfaction  # Future placeholder

    def summary(self) -> dict[str, Any]:
        return {
            "total_active_projects": self.total_active_projects,
            "portfolio_health_score": self.portfolio_health_score,
            "resource_utilization_percent": self.resource_utilization_percent,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_active_projects": self.total_active_projects,
            "portfolio_health_score": self.portfolio_health_score,
            "average_delivery_health": self.average_delivery_health,
            "resource_utilization_percent": self.resource_utilization_percent,
            "projects_by_industry": dict(self.projects_by_industry),
            "projects_by_status": dict(self.projects_by_status),
            "critical_project_count": self.critical_project_count,
            "capacity_remaining": self.capacity_remaining,
            "knowledge_assets_generated": self.knowledge_assets_generated,
            "average_client_satisfaction": self.average_client_satisfaction,
        }


class PortfolioRecommendation:
    def __init__(
        self,
        recommendation_id: str,
        title: str,
        description: str,
        priority: str,
        evidence: list[str],
        recommended_action: str,
    ) -> None:
        if not recommendation_id:
            raise ValueError("Recommendation ID is required.")
        if not evidence:
            raise ValueError("Every recommendation must include supporting evidence.")

        self.recommendation_id = recommendation_id
        self.title = title or "Advisory Recommendation"
        self.description = description or ""
        self.priority = priority or "MEDIUM"
        self.evidence = list(evidence)
        self.recommended_action = recommended_action or "Review at next executive briefing"

    def summary(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "priority": self.priority,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "evidence": list(self.evidence),
            "recommended_action": self.recommended_action,
        }


class PortfolioRisk:
    def __init__(
        self,
        risk_id: str,
        title: str,
        description: str,
        severity: str,
        impacted_projects: list[str],
        mitigation_strategy: str,
    ) -> None:
        if not risk_id:
            raise ValueError("Risk ID is required.")
        if not title:
            raise ValueError("Risk title is required.")

        self.risk_id = risk_id
        self.title = title
        self.description = description or ""
        self.severity = severity or "MEDIUM"
        self.impacted_projects = list(impacted_projects or [])
        self.mitigation_strategy = mitigation_strategy or "To be defined by executives"

    def summary(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "title": self.title,
            "severity": self.severity,
            "impacted_project_count": len(self.impacted_projects),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "impacted_projects": list(self.impacted_projects),
            "mitigation_strategy": self.mitigation_strategy,
        }


class CapacityForecast:
    def __init__(
        self,
        total_workers: int,
        available_workers: int,
        busy_workers: int,
        unassigned_tasks_portfolio: int,
        bottleneck_roles: list[str],
        capacity_status: str,
    ) -> None:
        self.total_workers = max(0, total_workers)
        self.available_workers = max(0, available_workers)
        self.busy_workers = max(0, busy_workers)
        self.unassigned_tasks_portfolio = max(0, unassigned_tasks_portfolio)
        self.bottleneck_roles = list(bottleneck_roles or [])
        self.capacity_status = capacity_status or "HEALTHY"

    def summary(self) -> dict[str, Any]:
        return {
            "total_workers": self.total_workers,
            "capacity_status": self.capacity_status,
            "unassigned_tasks": self.unassigned_tasks_portfolio,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_workers": self.total_workers,
            "available_workers": self.available_workers,
            "busy_workers": self.busy_workers,
            "unassigned_tasks_portfolio": self.unassigned_tasks_portfolio,
            "bottleneck_roles": list(self.bottleneck_roles),
            "capacity_status": self.capacity_status,
        }


class PortfolioReport:
    def __init__(
        self,
        report_id: str,
        metrics: PortfolioMetrics,
        capacity_forecast: CapacityForecast,
        active_projects: list[dict[str, Any]],
        completed_projects: list[dict[str, Any]],
        at_risk_projects: list[dict[str, Any]],
        critical_projects: list[dict[str, Any]],
        executive_workload: dict[str, Any],
        revenue_pipeline: dict[str, Any],
        strategic_opportunities: list[str],
        ceo_priority_list: list[PortfolioRecommendation | PortfolioRisk],
        recommendations: list[PortfolioRecommendation],
        risks: list[PortfolioRisk],
        created_at: str | None = None,
    ) -> None:
        if not report_id:
            raise ValueError("Report ID is required.")
        if metrics is None:
            raise ValueError("Metrics is required.")
        if capacity_forecast is None:
            raise ValueError("Capacity Forecast is required.")

        self.report_id = report_id
        self.metrics = metrics
        self.capacity_forecast = capacity_forecast
        self.active_projects = list(active_projects or [])
        self.completed_projects = list(completed_projects or [])
        self.at_risk_projects = list(at_risk_projects or [])
        self.critical_projects = list(critical_projects or [])
        self.executive_workload = dict(executive_workload or {})
        self.revenue_pipeline = dict(revenue_pipeline or {})
        self.strategic_opportunities = list(strategic_opportunities or [])
        self.ceo_priority_list = list(ceo_priority_list or [])
        self.recommendations = list(recommendations or [])
        self.risks = list(risks or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "portfolio_health_score": self.metrics.portfolio_health_score,
            "active_project_count": len(self.active_projects),
            "at_risk_project_count": len(self.at_risk_projects),
            "critical_project_count": len(self.critical_projects),
            "capacity_status": self.capacity_forecast.capacity_status,
            "recommendation_count": len(self.recommendations),
            "risk_count": len(self.risks),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "metrics": self.metrics.to_dict(),
            "capacity_forecast": self.capacity_forecast.to_dict(),
            "active_projects": list(self.active_projects),
            "completed_projects": list(self.completed_projects),
            "at_risk_projects": list(self.at_risk_projects),
            "critical_projects": list(self.critical_projects),
            "executive_workload": dict(self.executive_workload),
            "revenue_pipeline": dict(self.revenue_pipeline),
            "strategic_opportunities": list(self.strategic_opportunities),
            "ceo_priority_list": [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in self.ceo_priority_list
            ],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "risks": [r.to_dict() for r in self.risks],
            "summary": self.summary(),
            "created_at": self.created_at,
        }
