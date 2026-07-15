import logging
from typing import Any

from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.delivery_status_report import DeliveryStatusReport
from core.resource_allocation_plan import ResourceAllocationPlan
from core.business_transformation_plan import BusinessTransformationPlan
from core.portfolio_report import (
    PortfolioMetrics,
    PortfolioRecommendation,
    PortfolioRisk,
    CapacityForecast,
    PortfolioReport,
)

LOGGER = logging.getLogger(__name__)


class PortfolioManagementEngine:
    """Stateless engine providing a macro-level, real-time view of the entire
    client portfolio.

    The engine is purely advisory. It never modifies any underlying project, worker,
    or execution data.
    """

    def __init__(self) -> None:
        self._report_counter = 1
        self._recommendation_counter = 1
        self._risk_counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_portfolio(
        self,
        project_registry: ProjectRegistry,
        worker_registry: WorkerRegistry,
        delivery_reports: list[DeliveryStatusReport] | None = None,
        allocation_plans: list[ResourceAllocationPlan] | None = None,
        executive_briefing: dict[str, Any] | None = None,
        transformation_plans: list[BusinessTransformationPlan] | None = None,
    ) -> PortfolioReport:
        """Produce a PortfolioReport summarizing the company's entire client portfolio."""
        if project_registry is None:
            raise ValueError("ProjectRegistry is required.")
        if worker_registry is None:
            raise ValueError("WorkerRegistry is required.")

        report_id = self._next_report_id()
        LOGGER.info("object_id=%s action=analyze_portfolio actor=system status=DRAFT", report_id)

        delivery_reports = delivery_reports or []
        allocation_plans = allocation_plans or []
        executive_briefing = executive_briefing or {}
        transformation_plans = transformation_plans or []

        # Gather base entities
        all_projects = project_registry.list_projects()
        all_workers = worker_registry.list_workers()

        # ---- Categorize Projects -----------------------------------------
        active_projects = []
        completed_projects = []
        at_risk_projects = []
        critical_projects = []
        projects_by_status: dict[str, int] = {}

        # Pre-process delivery reports for fast lookup
        delivery_by_project = {
            getattr(r, "project_id", r.project_id): r for r in delivery_reports
        }

        # Health mapping
        # HEALTHY = 1.0, WATCH = 0.8, WARNING = 0.5, AT_RISK = 0.0, CRITICAL = 0.0
        health_scores = []
        
        for project in all_projects:
            status = getattr(getattr(project, "status", None), "value", getattr(project, "status", "UNKNOWN"))
            projects_by_status[status] = projects_by_status.get(status, 0) + 1
            proj_dict = project.summary() if hasattr(project, "summary") else {}
            
            if status == "ACTIVE":
                report = delivery_by_project.get(getattr(project, "id", None))
                health_str = getattr(report, "health_status", "HEALTHY") if report else "HEALTHY"
                proj_dict["health_status"] = health_str
                active_projects.append(proj_dict)
                
                # Derive health score
                score = 1.0
                if health_str == "WATCH":
                    score = 0.8
                elif health_str == "WARNING":
                    score = 0.5
                    at_risk_projects.append(proj_dict)
                elif health_str in ("AT_RISK", "CRITICAL"):
                    score = 0.0
                    at_risk_projects.append(proj_dict)
                    if health_str == "CRITICAL":
                        critical_projects.append(proj_dict)
                health_scores.append(score)

            elif status == "COMPLETED":
                completed_projects.append(proj_dict)

        # Average delivery health
        avg_delivery_health = sum(health_scores) / len(health_scores) if health_scores else 1.0
        
        # Determine portfolio health score (could be weighted by revenue in v2, for now simple avg)
        portfolio_health_score = avg_delivery_health

        # ---- Capacity and Utilization ------------------------------------
        available_workers = 0
        busy_workers = 0
        for worker in all_workers:
            status = getattr(getattr(worker, "status", None), "value", getattr(worker, "status", "UNKNOWN"))
            if status == "AVAILABLE":
                available_workers += 1
            elif status == "BUSY":
                busy_workers += 1

        total_workers = len(all_workers)
        utilization_percent = (busy_workers / total_workers * 100.0) if total_workers > 0 else 0.0

        # Unassigned tasks from allocation plans
        unassigned_tasks = sum(len(getattr(p, "unassigned_tasks", [])) for p in allocation_plans)

        capacity_status = "HEALTHY"
        if utilization_percent > 90.0 or unassigned_tasks > available_workers:
            capacity_status = "CRITICAL"
        elif utilization_percent > 75.0 or unassigned_tasks > 0:
            capacity_status = "WARNING"

        capacity_forecast = CapacityForecast(
            total_workers=total_workers,
            available_workers=available_workers,
            busy_workers=busy_workers,
            unassigned_tasks_portfolio=unassigned_tasks,
            bottleneck_roles=[],  # Can be expanded to infer from unassigned tasks
            capacity_status=capacity_status,
        )

        # ---- Build Metrics -----------------------------------------------
        metrics = PortfolioMetrics(
            total_active_projects=len(active_projects),
            portfolio_health_score=portfolio_health_score,
            average_delivery_health=avg_delivery_health,
            resource_utilization_percent=utilization_percent,
            projects_by_industry={"Technology": len(all_projects)},  # Placeholder logic
            projects_by_status=projects_by_status,
            critical_project_count=len(critical_projects),
            capacity_remaining=available_workers,
            knowledge_assets_generated=len(completed_projects) * 2,  # Approximation
            average_client_satisfaction=None,  # V2 Placeholder
        )

        # ---- Executive Workload ------------------------------------------
        executive_workload = executive_briefing.get("executive_availability", {})
        
        # ---- Revenue Pipeline --------------------------------------------
        # Volume-based placeholder
        planned_count = projects_by_status.get("PLANNED", 0)
        revenue_pipeline = {
            "planned_projects_count": planned_count,
            "pipeline_status": "STRONG" if planned_count > 0 else "WEAK",
        }

        # ---- Strategic Opportunities -------------------------------------
        strategic_opportunities = []
        if capacity_forecast.available_workers > 2:
            strategic_opportunities.append("Excess capacity allows for accelerating pipeline projects.")
        for tp in transformation_plans:
            strategic_opportunities.append(
                f"Transformation plan {getattr(tp, 'plan_id', 'Unknown')} active. Identify cross-sell."
            )

        # ---- Risks & Recommendations -------------------------------------
        risks = self._build_portfolio_risks(
            active_projects, at_risk_projects, critical_projects, capacity_forecast
        )
        recommendations = self._build_recommendations(
            metrics, capacity_forecast, risks, at_risk_projects
        )

        # ---- CEO Priority List -------------------------------------------
        ceo_priority_list: list[Any] = []
        # Add critical risks
        for r in risks:
            if r.severity == "CRITICAL":
                ceo_priority_list.append(r)
        # Add high priority recommendations
        for rec in recommendations:
            if rec.priority in ("HIGH", "CRITICAL"):
                ceo_priority_list.append(rec)

        LOGGER.info("object_id=%s action=analyze_portfolio actor=system status=READY active=%d", 
                    report_id, len(active_projects))

        return PortfolioReport(
            report_id=report_id,
            metrics=metrics,
            capacity_forecast=capacity_forecast,
            active_projects=active_projects,
            completed_projects=completed_projects,
            at_risk_projects=at_risk_projects,
            critical_projects=critical_projects,
            executive_workload=executive_workload,
            revenue_pipeline=revenue_pipeline,
            strategic_opportunities=strategic_opportunities,
            ceo_priority_list=ceo_priority_list,
            recommendations=recommendations,
            risks=risks,
        )

    # ------------------------------------------------------------------
    # Private Builders
    # ------------------------------------------------------------------

    def _build_portfolio_risks(
        self,
        active_projects: list[dict[str, Any]],
        at_risk_projects: list[dict[str, Any]],
        critical_projects: list[dict[str, Any]],
        capacity_forecast: CapacityForecast,
    ) -> list[PortfolioRisk]:
        risks: list[PortfolioRisk] = []

        if capacity_forecast.capacity_status in ("CRITICAL", "WARNING"):
            risks.append(PortfolioRisk(
                risk_id=self._next_risk_id(),
                title="Portfolio Resource Bottleneck",
                description="High utilization or unassigned tasks indicating systemic resource constraint.",
                severity=capacity_forecast.capacity_status,
                impacted_projects=[p.get("id", "Unknown") for p in active_projects],
                mitigation_strategy="Halt new project intake or reassign lower priority workers.",
            ))
            
        if len(critical_projects) > 0:
            risks.append(PortfolioRisk(
                risk_id=self._next_risk_id(),
                title="Critical Projects Requiring Intervention",
                description=f"{len(critical_projects)} projects are in critical state.",
                severity="CRITICAL",
                impacted_projects=[p.get("id", "Unknown") for p in critical_projects],
                mitigation_strategy="Immediate CEO intervention and steering committee review.",
            ))

        if len(at_risk_projects) > (len(active_projects) * 0.3) and len(active_projects) > 0:
            risks.append(PortfolioRisk(
                risk_id=self._next_risk_id(),
                title="High Proportion of At-Risk Projects",
                description="More than 30% of the active portfolio is at risk or warning.",
                severity="HIGH",
                impacted_projects=[p.get("id", "Unknown") for p in at_risk_projects],
                mitigation_strategy="Conduct portfolio-wide delivery audit.",
            ))

        return risks

    def _build_recommendations(
        self,
        metrics: PortfolioMetrics,
        capacity_forecast: CapacityForecast,
        risks: list[PortfolioRisk],
        at_risk_projects: list[dict[str, Any]],
    ) -> list[PortfolioRecommendation]:
        recs: list[PortfolioRecommendation] = []

        if capacity_forecast.capacity_status == "CRITICAL":
            recs.append(PortfolioRecommendation(
                recommendation_id=self._next_recommendation_id(),
                title="Freeze New Project Initiation",
                description="Systemic resource constraints threaten ongoing delivery.",
                priority="CRITICAL",
                evidence=[
                    f"Utilization is {metrics.resource_utilization_percent:.1f}%",
                    f"Unassigned tasks: {capacity_forecast.unassigned_tasks_portfolio}",
                ],
                recommended_action="Do not move PLANNED projects to ACTIVE until utilization drops below 85%.",
            ))

        if len(at_risk_projects) > 0:
            recs.append(PortfolioRecommendation(
                recommendation_id=self._next_recommendation_id(),
                title="Review At-Risk Deliveries",
                description="Several projects have dropped below HEALTHY status.",
                priority="HIGH",
                evidence=[
                    f"{len(at_risk_projects)} projects in WARNING/AT_RISK/CRITICAL state.",
                    f"Average delivery health is {metrics.average_delivery_health:.2f}.",
                ],
                recommended_action="Schedule delivery reviews for all at-risk projects this week.",
            ))
            
        if metrics.resource_utilization_percent < 50.0 and metrics.total_active_projects > 0:
            recs.append(PortfolioRecommendation(
                recommendation_id=self._next_recommendation_id(),
                title="Accelerate Planned Projects",
                description="Low resource utilization indicates capacity to take on more work.",
                priority="MEDIUM",
                evidence=[
                    f"Utilization is only {metrics.resource_utilization_percent:.1f}%.",
                    f"{capacity_forecast.available_workers} workers available.",
                ],
                recommended_action="Begin kickoff for next planned projects in the pipeline.",
            ))

        # Ensure we always return at least one generic recommendation if portfolio is active
        if not recs and metrics.total_active_projects > 0:
            recs.append(PortfolioRecommendation(
                recommendation_id=self._next_recommendation_id(),
                title="Maintain Current Delivery Pace",
                description="Portfolio is healthy and operating within capacity.",
                priority="LOW",
                evidence=[
                    f"Portfolio health score: {metrics.portfolio_health_score:.2f}",
                    f"Utilization: {metrics.resource_utilization_percent:.1f}%",
                ],
                recommended_action="Continue standard monitoring.",
            ))

        return recs

    # ------------------------------------------------------------------
    # ID Generators
    # ------------------------------------------------------------------

    def _next_report_id(self) -> str:
        rid = f"PRT-{self._report_counter:04d}"
        self._report_counter += 1
        return rid

    def _next_recommendation_id(self) -> str:
        rid = f"PREC-{self._recommendation_counter:04d}"
        self._recommendation_counter += 1
        return rid

    def _next_risk_id(self) -> str:
        rid = f"PRSK-{self._risk_counter:04d}"
        self._risk_counter += 1
        return rid
