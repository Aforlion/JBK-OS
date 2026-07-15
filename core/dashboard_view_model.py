from __future__ import annotations

from typing import Any


class ExecutiveCard:
    """View model representing a card on the executive dashboard."""

    def __init__(self, card_id: str, title: str, category: str, content: str, priority: str = "MEDIUM") -> None:
        self.card_id = card_id
        self.title = title
        self.category = category
        self.content = content
        self.priority = priority

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "priority": self.priority,
        }


class ProjectCard:
    """View model representing a project status card."""

    def __init__(self, project_id: str, name: str, progress_pct: float, status: str, owner: str, risk_level: str) -> None:
        self.project_id = project_id
        self.name = name
        self.progress_pct = progress_pct
        self.status = status
        self.owner = owner
        self.risk_level = risk_level

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "progress_pct": self.progress_pct,
            "status": self.status,
            "owner": self.owner,
            "risk_level": self.risk_level,
        }


class AlertCard:
    """View model representing an alert card."""

    def __init__(self, alert_id: str, severity: str, title: str, description: str, source_engine: str, action: str = "") -> None:
        self.alert_id = alert_id
        self.severity = severity
        self.title = title
        self.description = description
        self.source_engine = source_engine
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "source_engine": self.source_engine,
            "action": self.action,
        }


class KPIWidget:
    """View model representing a single KPI widget."""

    def __init__(self, name: str, value: Any, trend: str, status: str, target: Any = None) -> None:
        self.name = name
        self.value = value
        self.trend = trend
        self.status = status
        self.target = target

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "trend": self.trend,
            "status": self.status,
            "target": self.target,
        }


class ConversationWidget:
    """View model representing the AI Assistant conversation panel."""

    def __init__(self, conversation_id: str, status: str, messages: list[dict[str, Any]] | None = None, suggestions: list[str] | None = None) -> None:
        self.conversation_id = conversation_id
        self.status = status
        self.messages = messages or []
        self.suggestions = suggestions or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "status": self.status,
            "messages": self.messages,
            "suggestions": self.suggestions,
        }


class ActivityFeedItem:
    """View model representing a single item in the Activity Feed."""

    def __init__(self, item_id: str, title: str, category: str, timestamp: str, details: str = "", severity: str = "INFO") -> None:
        self.item_id = item_id
        self.title = title
        self.category = category
        self.timestamp = timestamp
        self.details = details
        self.severity = severity

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "category": self.category,
            "timestamp": self.timestamp,
            "details": self.details,
            "severity": self.severity,
        }


class QuickAction:
    """View model representing an executive quick action button."""

    def __init__(self, action_id: str, label: str, target_route: str, icon: str = "") -> None:
        self.action_id = action_id
        self.label = label
        self.target_route = target_route
        self.icon = icon

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "target_route": self.target_route,
            "icon": self.icon,
        }


class NavigationSection:
    """View model representing a section in the left navigation panel."""

    def __init__(self, title: str, items: list[dict[str, str]]) -> None:
        self.title = title
        self.items = items

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "items": self.items,
        }


class DashboardViewModel:
    """Top-level Dashboard View Model aggregation."""

    def __init__(
        self,
        company_status: str,
        kpis: list[KPIWidget],
        alerts: list[AlertCard],
        projects: list[ProjectCard],
        activity_feed: list[ActivityFeedItem],
        conversation: ConversationWidget | None = None,
        quick_actions: list[QuickAction] | None = None,
        navigation: list[NavigationSection] | None = None,
    ) -> None:
        self.company_status = company_status
        self.kpis = kpis
        self.alerts = alerts
        self.projects = projects
        self.activity_feed = activity_feed
        self.conversation = conversation
        self.quick_actions = quick_actions or []
        self.navigation = navigation or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_status": self.company_status,
            "kpis": [k.to_dict() for k in self.kpis],
            "alerts": [a.to_dict() for a in self.alerts],
            "projects": [p.to_dict() for p in self.projects],
            "activity_feed": [af.to_dict() for af in self.activity_feed],
            "conversation": self.conversation.to_dict() if self.conversation else None,
            "quick_actions": [qa.to_dict() for qa in self.quick_actions],
            "navigation": [n.to_dict() for n in self.navigation],
        }
