from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.executive_kpi import ExecutiveKPI
from core.dashboard_alert import DashboardAlert
from core.dashboard_section import DashboardSection
from core.executive_dashboard import ExecutiveDashboard

LOGGER = logging.getLogger(__name__)


class ExecutiveDashboardEngine:
    """Read-only Executive Dashboard Aggregator.

    BR-046-001: Stateless generation.
    BR-046-002: Never modifies operational data.
    BR-046-006: Unavailable subsystems show "Unavailable" gracefully.
    """

    def __init__(
        self,
        portfolio_engine: Any = None,
        financial_engine: Any = None,
        crm_engine: Any = None,
        delivery_engine: Any = None,
        strategic_engine: Any = None,
        autonomous_engine: Any = None,
        client_success_engine: Any = None,
        memory_engine: Any = None,
        ai_gateway: Any = None,
        communication_engine: Any = None,
        briefing_engine: Any = None,
    ) -> None:
        self.portfolio_engine = portfolio_engine
        self.financial_engine = financial_engine
        self.crm_engine = crm_engine
        self.delivery_engine = delivery_engine
        self.strategic_engine = strategic_engine
        self.autonomous_engine = autonomous_engine
        self.client_success_engine = client_success_engine
        self.memory_engine = memory_engine
        self.ai_gateway = ai_gateway
        self.communication_engine = communication_engine
        self.briefing_engine = briefing_engine
        self._dashboard_counter = 1

    def generate_dashboard(self) -> ExecutiveDashboard:
        """Query all active subsystems, aggregate KPIs, sort alerts, and generate dashboard."""
        sections: list[DashboardSection] = []
        alerts: list[DashboardAlert] = []
        recommendations: list[dict[str, str]] = []

        # Subsystem Querying (Enforcing BR-046-006: failure resilience)

        # 1. Executive Briefing
        try:
            if self.briefing_engine:
                # Mock or real call
                briefing_data = self.briefing_engine.get_briefing_summary()
                sections.append(DashboardSection(
                    title="Executive Briefing",
                    source_engine="AIExecutiveAssistant",
                    status="HEALTHY",
                    summary=briefing_data.get("summary", "Briefing active."),
                    metrics=briefing_data.get("metrics", {}),
                ))
            else:
                sections.append(DashboardSection(
                    title="Executive Briefing",
                    source_engine="AIExecutiveAssistant",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Briefing Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Executive Briefing",
                source_engine="AIExecutiveAssistant",
                status="UNAVAILABLE",
            ))

        # 2. Portfolio Health
        try:
            if self.portfolio_engine:
                portfolio_report = self.portfolio_engine.generate_report()
                sections.append(DashboardSection(
                    title="Portfolio Health",
                    source_engine="PortfolioEngine",
                    status="HEALTHY",
                    summary=f"Total projects: {portfolio_report.get('total_projects', 0)}",
                    metrics={
                        "total_projects": portfolio_report.get("total_projects", 0),
                        "at_risk_count": portfolio_report.get("at_risk_count", 0),
                    },
                ))
            else:
                sections.append(DashboardSection(
                    title="Portfolio Health",
                    source_engine="PortfolioEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Portfolio Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Portfolio Health",
                source_engine="PortfolioEngine",
                status="UNAVAILABLE",
            ))

        # 3. Financial Overview
        try:
            if self.financial_engine:
                fin_report = self.financial_engine.generate_financial_report()
                sections.append(DashboardSection(
                    title="Financial Overview",
                    source_engine="FinancialOperationsEngine",
                    status="HEALTHY" if fin_report.cash_health == "Healthy" else "WARNING",
                    summary=fin_report.executive_summary,
                    metrics=fin_report.kpis,
                ))
                # Collect financial recommendations (BR-046-005)
                for rec in fin_report.recommendations:
                    recommendations.append({
                        "action": rec.get("action", ""),
                        "reasoning": rec.get("why", ""),
                        "source_engine": "FinancialOperationsEngine",
                    })
            else:
                sections.append(DashboardSection(
                    title="Financial Overview",
                    source_engine="FinancialOperationsEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Financial Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Financial Overview",
                source_engine="FinancialOperationsEngine",
                status="UNAVAILABLE",
            ))

        # 4. Client Pipeline (CRM)
        try:
            if self.crm_engine:
                clients = self.crm_engine.list_clients()
                sections.append(DashboardSection(
                    title="Client Pipeline",
                    source_engine="CRMEngine",
                    status="HEALTHY",
                    summary=f"Active clients: {len(clients)}",
                    metrics={"total_clients": len(clients)},
                ))
            else:
                sections.append(DashboardSection(
                    title="Client Pipeline",
                    source_engine="CRMEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("CRM Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Client Pipeline",
                source_engine="CRMEngine",
                status="UNAVAILABLE",
            ))

        # 5. Active Projects (Delivery Supervision)
        try:
            if self.delivery_engine:
                del_report = self.delivery_engine.generate_delivery_status_report()
                sections.append(DashboardSection(
                    title="Active Projects",
                    source_engine="DeliverySupervisionEngine",
                    status="HEALTHY" if del_report.get("status") == "HEALTHY" else "WARNING",
                    summary=f"Monitoring {len(del_report.get('projects', []))} active projects.",
                    metrics={
                        "active_count": len(del_report.get("projects", [])),
                        "at_risk_count": del_report.get("at_risk_count", 0),
                    },
                ))
            else:
                sections.append(DashboardSection(
                    title="Active Projects",
                    source_engine="DeliverySupervisionEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Delivery Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Active Projects",
                source_engine="DeliverySupervisionEngine",
                status="UNAVAILABLE",
            ))

        # 6. Strategic Intelligence
        try:
            if self.strategic_engine:
                strat_report = self.strategic_engine.generate_report()
                sections.append(DashboardSection(
                    title="Strategic Intelligence",
                    source_engine="StrategicIntelligenceEngine",
                    status="HEALTHY",
                    summary=strat_report.get("summary", "Strategic signals clear."),
                    metrics=strat_report.get("metrics", {}),
                ))
            else:
                sections.append(DashboardSection(
                    title="Strategic Intelligence",
                    source_engine="StrategicIntelligenceEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Strategic Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Strategic Intelligence",
                source_engine="StrategicIntelligenceEngine",
                status="UNAVAILABLE",
            ))

        # 7. Company Health (Autonomous Operations)
        try:
            if self.autonomous_engine:
                auto_report = self.autonomous_engine.generate_health_report()
                sections.append(DashboardSection(
                    title="Company Health",
                    source_engine="AutonomousOperationsEngine",
                    status="HEALTHY",
                    summary=f"Current health score: {auto_report.get('health_score', 100)}",
                    metrics=auto_report,
                ))
            else:
                sections.append(DashboardSection(
                    title="Company Health",
                    source_engine="AutonomousOperationsEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Autonomous Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Company Health",
                source_engine="AutonomousOperationsEngine",
                status="UNAVAILABLE",
            ))

        # 8. Client Success
        try:
            if self.client_success_engine and self.crm_engine:
                clients = self.crm_engine.list_clients()
                total_satisfaction = 0.0
                valid_count = 0
                for c in clients:
                    try:
                        success_rep = self.client_success_engine.evaluate_success(c)
                        total_satisfaction += c.satisfaction_score
                        valid_count += 1
                        # Collect success risk alerts
                        for risk in success_rep.risk_alerts:
                            alerts.append(DashboardAlert(
                                alert_id=f"ALT-S{len(alerts)+1:03d}",
                                severity="HIGH" if risk.severity == "High" else "MEDIUM",
                                category="Client Success",
                                title=f"Client Risk: {c.company}",
                                description=risk.description,
                                recommended_action="Initiate Client Success outreach.",
                                source_engine="ClientSuccessEngine",
                            ))
                    except Exception:
                        pass

                avg_satisfaction = round(total_satisfaction / valid_count, 1) if valid_count > 0 else 0.0
                sections.append(DashboardSection(
                    title="Client Success",
                    source_engine="ClientSuccessEngine",
                    status="HEALTHY" if avg_satisfaction >= 3.5 else "WARNING",
                    summary=f"Average Client Satisfaction: {avg_satisfaction}",
                    metrics={"average_satisfaction": avg_satisfaction},
                ))
            else:
                sections.append(DashboardSection(
                    title="Client Success",
                    source_engine="ClientSuccessEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Client Success Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Client Success",
                source_engine="ClientSuccessEngine",
                status="UNAVAILABLE",
            ))

        # 9. Knowledge Growth (Memory Engine)
        try:
            if self.memory_engine:
                memory_rep = self.memory_engine.generate_report()
                sections.append(DashboardSection(
                    title="Knowledge Growth",
                    source_engine="OrganizationalMemoryEngine",
                    status="HEALTHY",
                    summary=f"Total memories stored: {memory_rep.get('total_memories', 0)}",
                    metrics=memory_rep,
                ))
            else:
                sections.append(DashboardSection(
                    title="Knowledge Growth",
                    source_engine="OrganizationalMemoryEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Memory Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Knowledge Growth",
                source_engine="OrganizationalMemoryEngine",
                status="UNAVAILABLE",
            ))

        # 10. AI Usage (AI Gateway)
        try:
            if self.ai_gateway:
                gateway_stats = self.ai_gateway.get_usage_summary()
                sections.append(DashboardSection(
                    title="AI Usage",
                    source_engine="AIGateway",
                    status="HEALTHY",
                    summary=f"API Calls: {gateway_stats.get('total_calls', 0)}",
                    metrics=gateway_stats,
                ))
            else:
                sections.append(DashboardSection(
                    title="AI Usage",
                    source_engine="AIGateway",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("AI Gateway query failed: %s", e)
            sections.append(DashboardSection(
                title="AI Usage",
                source_engine="AIGateway",
                status="UNAVAILABLE",
            ))

        # 11. Notifications (Communication Engine)
        try:
            if self.communication_engine:
                comm_report = self.communication_engine.generate_report()
                sections.append(DashboardSection(
                    title="Notifications",
                    source_engine="CommunicationEngine",
                    status="HEALTHY",
                    summary=f"Unread Notifications: {comm_report.unread_notifications}",
                    metrics=comm_report.to_dict(),
                ))
                # Add communication warnings/failures
                for fail in comm_report.failures:
                    alerts.append(DashboardAlert(
                        alert_id=f"ALT-C{len(alerts)+1:03d}",
                        severity="MEDIUM",
                        category="Communications",
                        title="Delivery Failure",
                        description=f"Message to {fail.get('recipient')} failed.",
                        recommended_action="Retry sending message.",
                        source_engine="CommunicationEngine",
                    ))
            else:
                sections.append(DashboardSection(
                    title="Notifications",
                    source_engine="CommunicationEngine",
                    status="UNAVAILABLE",
                ))
        except Exception as e:
            LOGGER.error("Communication Engine query failed: %s", e)
            sections.append(DashboardSection(
                title="Notifications",
                source_engine="CommunicationEngine",
                status="UNAVAILABLE",
            ))

        # Sort alerts (CRITICAL first, BR-046-004)
        alerts.sort(key=lambda a: a.severity_weight, reverse=True)

        # Company Health Score aggregation (BR-046-007)
        company_health_score = self._calculate_company_health(sections)

        # Build list of 11 KPIs
        kpis = self._build_kpis(sections, company_health_score)

        # Executive summary
        executive_summary = (
            f"Overall Company Health: {company_health_score:.1f}/100. "
            f"Active Projects: {self._get_metric_val(sections, 'Active Projects', 'active_count', 0)}. "
            f"Outstanding Invoices: {self._get_metric_val(sections, 'Financial Overview', 'outstanding_invoices_count', 0)}. "
            f"Aged AR Issues: {self._get_metric_val(sections, 'Financial Overview', 'accounts_receivable_aged_30d', 0)}."
        )

        dashboard_id = f"DSH-{self._dashboard_counter:04d}"
        self._dashboard_counter += 1

        return ExecutiveDashboard(
            dashboard_id=dashboard_id,
            company_status="WARNING" if any(s.status == "CRITICAL" for s in sections) or len(alerts) > 3 else "HEALTHY",
            sections=sections,
            alerts=alerts,
            kpis=kpis,
            recommendations=recommendations,
            executive_summary=executive_summary,
        )

    def _calculate_company_health(self, sections: list[DashboardSection]) -> float:
        """BR-046-007: Aggregates Company Health from six distinct sources:
        Portfolio, Financial, Delivery, Strategic, Workforce (Autonomous), Client Success.
        """
        score_sum = 0.0
        counted = 0
        target_sections = {
            "Portfolio Health": 1.0,
            "Financial Overview": 1.0,
            "Active Projects": 1.0,
            "Strategic Intelligence": 1.0,
            "Company Health": 1.0,  # Workforce/Autonomous operations
            "Client Success": 1.0,
        }

        for sec in sections:
            if sec.title in target_sections:
                if sec.status == "HEALTHY":
                    score_sum += 100.0
                elif sec.status == "WARNING":
                    score_sum += 70.0
                elif sec.status == "CRITICAL":
                    score_sum += 40.0
                elif sec.status == "UNAVAILABLE":
                    score_sum += 50.0  # neutral penalty for missing data
                counted += 1

        if counted == 0:
            return 100.0
        return round(score_sum / counted, 1)

    def _build_kpis(self, sections: list[DashboardSection], health_score: float) -> list[ExecutiveKPI]:
        """Calculates and constructs all required 11 KPIs."""
        kpis = []

        # 1. Total Clients
        kpis.append(ExecutiveKPI(
            name="Total Clients",
            value=self._get_metric_val(sections, "Client Pipeline", "total_clients", 0),
            trend="STABLE",
            status="ON_TRACK",
        ))

        # 2. Active Projects
        kpis.append(ExecutiveKPI(
            name="Active Projects",
            value=self._get_metric_val(sections, "Active Projects", "active_count", 0),
            trend="UP",
            status="ON_TRACK",
        ))

        # 3. Projects At Risk
        at_risk = self._get_metric_val(sections, "Active Projects", "at_risk_count", 0)
        kpis.append(ExecutiveKPI(
            name="Projects At Risk",
            value=at_risk,
            trend="DOWN" if at_risk == 0 else "UP",
            status="CRITICAL" if at_risk > 1 else "ON_TRACK",
        ))

        # 4. Monthly Revenue
        kpis.append(ExecutiveKPI(
            name="Monthly Revenue",
            value=self._get_metric_val(sections, "Financial Overview", "total_revenue", 0.0),
            trend="STABLE",
            status="ON_TRACK",
        ))

        # 5. Outstanding Invoices
        out_inv = self._get_metric_val(sections, "Financial Overview", "outstanding_invoices_count", 0)
        kpis.append(ExecutiveKPI(
            name="Outstanding Invoices",
            value=out_inv,
            trend="STABLE",
            status="AT_RISK" if out_inv > 3 else "ON_TRACK",
        ))

        # 6. Proposal Win Rate
        kpis.append(ExecutiveKPI(
            name="Proposal Win Rate",
            value=self._get_metric_val(sections, "Portfolio Health", "win_rate", 75.0),
            trend="STABLE",
            status="ON_TRACK",
        ))

        # 7. Average Client Health
        avg_health = self._get_metric_val(sections, "Client Success", "average_satisfaction", 5.0)
        kpis.append(ExecutiveKPI(
            name="Average Client Health",
            value=avg_health,
            trend="STABLE",
            status="ON_TRACK" if avg_health >= 4.0 else "AT_RISK",
        ))

        # 8. Knowledge Assets
        kpis.append(ExecutiveKPI(
            name="Knowledge Assets",
            value=self._get_metric_val(sections, "Knowledge Growth", "total_memories", 0),
            trend="UP",
            status="ON_TRACK",
        ))

        # 9. Executive Utilization
        kpis.append(ExecutiveKPI(
            name="Executive Utilization",
            value=self._get_metric_val(sections, "Company Health", "executive_utilization", 80.0),
            trend="STABLE",
            status="ON_TRACK",
        ))

        # 10. AI Cost
        kpis.append(ExecutiveKPI(
            name="AI Cost",
            value=self._get_metric_val(sections, "AI Usage", "total_cost", 0.0),
            trend="UP",
            status="ON_TRACK",
        ))

        # 11. Company Health Score
        kpis.append(ExecutiveKPI(
            name="Company Health Score",
            value=health_score,
            trend="STABLE",
            status="ON_TRACK" if health_score >= 80.0 else "AT_RISK",
        ))

        return kpis

    def _get_metric_val(self, sections: list[DashboardSection], title: str, metric_key: str, default: Any) -> Any:
        for s in sections:
            if s.title == title:
                return s.metrics.get(metric_key, default)
        return default
