from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.dashboard_view_model import (
    DashboardViewModel,
    ProjectCard,
    AlertCard,
    KPIWidget,
    ConversationWidget,
    ActivityFeedItem,
    QuickAction,
    NavigationSection,
)

LOGGER = logging.getLogger(__name__)


class ExecutiveConsoleController:
    """Orchestrates UI-safe views for the Executive Web Console.

    Contains NO business logic. Acts strictly as an adapter/converter layer.
    """

    def __init__(
        self,
        dashboard_engine: Any = None,
        portfolio_engine: Any = None,
        crm_engine: Any = None,
        delivery_engine: Any = None,
        ai_assistant: Any = None,
        strategic_engine: Any = None,
        meeting_engine: Any = None,
        communication_engine: Any = None,
        monitoring_engine: Any = None,
    ) -> None:
        self.dashboard_engine = dashboard_engine
        self.portfolio_engine = portfolio_engine
        self.crm_engine = crm_engine
        self.delivery_engine = delivery_engine
        self.ai_assistant = ai_assistant
        self.strategic_engine = strategic_engine
        self.meeting_engine = meeting_engine
        self.communication_engine = communication_engine
        self.monitoring_engine = monitoring_engine

    def load_dashboard(self) -> DashboardViewModel:
        """Loads and formats the dashboard view model, supporting graceful degradation."""
        # 1. Fetch backend dashboard state
        backend_db = None
        company_status = "HEALTHY" if self.dashboard_engine else "CRITICAL"
        kpis = []
        alerts = []

        if self.dashboard_engine:
            try:
                backend_db = self.dashboard_engine.generate_dashboard()
                company_status = backend_db.company_status
                for k in backend_db.kpis:
                    kpis.append(KPIWidget(
                        name=k.name,
                        value=k.value,
                        trend=k.trend,
                        status=k.status,
                        target=k.target,
                    ))
                for a in backend_db.alerts:
                    alerts.append(AlertCard(
                        alert_id=a.alert_id,
                        severity=a.severity,
                        title=a.title,
                        description=a.description,
                        source_engine=a.source_engine,
                        action=a.recommended_action,
                    ))
            except Exception as e:
                LOGGER.error("Dashboard Engine call failed in controller: %s", e)
                company_status = "CRITICAL"

        # Fallback if no backend dashboard engine
        if not kpis:
            kpis = [
                KPIWidget("Company Health Score", 50.0, "STABLE", "AT_RISK"),
                KPIWidget("Active Projects", 0, "UNKNOWN", "ON_TRACK"),
            ]

        # 2. Load projects
        projects = self.load_projects()

        # 3. Load activity feed
        feed = self.load_activity_feed()

        # 4. Load conversation widget
        conversation = self.load_conversations()

        # 5. Load quick actions
        quick_actions = [
            QuickAction("new_client", "New Client", "/api/actions/new-client", "user-plus"),
            QuickAction("briefing", "Executive Briefing", "/api/actions/briefing", "file-text"),
            QuickAction("view_projects", "View Projects", "/api/actions/view-projects", "briefcase"),
            QuickAction("start_meeting", "Start Meeting", "/api/actions/start-meeting", "video"),
        ]

        # 6. Load navigation
        navigation = [
            NavigationSection("Dashboard", [{"label": "Overview", "route": "/"}]),
            NavigationSection("Management", [
                {"label": "CRM", "route": "/crm"},
                {"label": "Projects", "route": "/projects"},
                {"label": "Finance", "route": "/finance"},
            ]),
        ]

        return DashboardViewModel(
            company_status=company_status,
            kpis=kpis,
            alerts=alerts,
            projects=projects,
            activity_feed=feed,
            conversation=conversation,
            quick_actions=quick_actions,
            navigation=navigation,
        )

    def load_projects(self) -> list[ProjectCard]:
        """Load projects view models with graceful degradation."""
        project_cards = []
        if self.delivery_engine:
            try:
                report = self.delivery_engine.generate_delivery_status_report()
                # If the report is a dictionary containing project list
                projects_list = report.get("projects", [])
                for p in projects_list:
                    # Depending on project model shape
                    pid = getattr(p, "project_id", str(p)) if not isinstance(p, dict) else p.get("project_id", "PROJ")
                    name = getattr(p, "name", f"Project {pid}") if not isinstance(p, dict) else p.get("name", "")
                    progress = getattr(p, "completion_pct", 50.0) if not isinstance(p, dict) else p.get("completion_pct", 50.0)
                    status = getattr(p, "status", "ACTIVE") if not isinstance(p, dict) else p.get("status", "ACTIVE")
                    owner = getattr(p, "owner", "System") if not isinstance(p, dict) else p.get("owner", "System")
                    risk = getattr(p, "risk_level", "LOW") if not isinstance(p, dict) else p.get("risk_level", "LOW")
                    project_cards.append(ProjectCard(
                        project_id=pid,
                        name=name,
                        progress_pct=progress,
                        status=status,
                        owner=owner,
                        risk_level=risk,
                    ))
            except Exception as e:
                LOGGER.error("Failed to load projects: %s", e)
        return project_cards

    def load_activity_feed(self) -> list[ActivityFeedItem]:
        """Load activity feed from communication engine or logs."""
        feed_items = []
        if self.communication_engine:
            try:
                log = self.communication_engine.get_audit_log()
                for entry in list(log.all_entries())[-10:]:
                    feed_items.append(ActivityFeedItem(
                        item_id=f"ACT-{entry.communication_id}",
                        title=entry.action,
                        category="System Log",
                        timestamp=entry.timestamp,
                        details=entry.details,
                    ))
            except Exception as e:
                LOGGER.error("Failed to load activity feed: %s", e)
        
        if not feed_items:
            feed_items = [
                ActivityFeedItem(
                    item_id="ACT-001",
                    title="Console Started",
                    category="System",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details="Executive Console started successfully.",
                )
            ]
        return feed_items

    def load_conversations(self) -> ConversationWidget:
        """Load AI Assistant conversation panel."""
        messages = []
        if self.ai_assistant:
            try:
                # Assumes context retrieval is possible
                # Otherwise, return default panel
                pass
            except Exception:
                pass
        return ConversationWidget(
            conversation_id="CONV-MAIN",
            status="ACTIVE",
            messages=messages,
            suggestions=[
                "Show company health",
                "Prepare proposal",
                "Review active projects",
                "Schedule executive meeting",
            ]
        )

    def search(self, query: str) -> list[dict[str, Any]]:
        """Global search across JBK-OS registries and engines."""
        results = []
        if not query or not query.strip():
            return results

        q = query.strip().lower()

        # 1. Search CRM
        if self.crm_engine:
            try:
                for c in self.crm_engine.list_clients():
                    if q in c.company.lower() or q in c.industry.lower():
                        results.append({
                            "type": "Client",
                            "id": c.client_id,
                            "title": c.company,
                            "subtitle": f"Industry: {c.industry} | Health: {c.relationship_status}",
                        })
            except Exception:
                pass

        # 2. Search Delivery/Projects
        if self.delivery_engine:
            try:
                # Mock registry search or list projects
                pass
            except Exception:
                pass

        return results

    def quick_action(self, action_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Trigger backend actions strictly via existing engines."""
        # Clean params
        params = params or {}
        
        if action_name == "new-client":
            if self.crm_engine:
                try:
                    c = self.crm_engine.register_client(
                        company=params.get("company", "New Client Corp"),
                        industry=params.get("industry", "General"),
                    )
                    return {"success": True, "details": f"Registered client: {c.company}"}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": "CRM Engine unavailable"}

        elif action_name == "briefing":
            if self.ai_assistant:
                try:
                    brief = self.ai_assistant.converse("Prepare startup briefing")
                    return {"success": True, "response": brief}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": "AI Assistant unavailable"}

        return {"success": False, "error": f"Unknown action: {action_name}"}
