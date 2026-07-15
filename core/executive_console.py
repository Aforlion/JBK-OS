from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


class ExecutiveConsole:
    def __init__(self, briefing_engine: Any) -> None:
        if briefing_engine is None:
            raise ValueError("Executive Briefing Engine is required.")
        self.briefing_engine = briefing_engine
        self.briefing_data: dict[str, Any] = {}

    def load(self) -> str:
        self.refresh()
        screen = [
            "Good Morning, Joel.",
            "",
            "=== Executive Briefing ===",
            self.render_briefing(),
            "",
            "=== Projects ===",
            self.render_projects(),
            "",
            "=== Workflows ===",
            self.render_workflows(),
            "",
            "=== CEO Attention ===",
            self.render_attention_items(),
            "",
            "Command Prompt"
        ]
        return "\n".join(screen)

    def refresh(self) -> None:
        self.briefing_data = self.briefing_engine.generate_daily_briefing()

    def render_briefing(self) -> str:
        if not self.briefing_data:
            return "No briefing data loaded."
        
        health = self.briefing_data.get("operational_health", "UNKNOWN")
        date = self.briefing_data.get("date", "UNKNOWN")
        attention_count = len(self.briefing_data.get("items_requiring_ceo_attention", []))
        
        lines = [
            f"Date: {date}",
            f"Operational Health: {health}",
            f"Today's Priorities: {attention_count} items requiring attention"
        ]
        return "\n".join(lines)

    def render_projects(self) -> str:
        if not self.briefing_data:
            return "No project data loaded."
            
        active = self.briefing_data.get("active_projects", [])
        completed = self.briefing_data.get("completed_projects", [])
        
        lines = [
            f"Active Projects ({len(active)}):"
        ]
        for p in active:
            lines.append(f"  - [{p.get('id')}] {p.get('title')} (Client: {p.get('client')})")
            
        lines.append(f"Completed Projects ({len(completed)}):")
        for p in completed:
            lines.append(f"  - [{p.get('id')}] {p.get('title')} (Client: {p.get('client')})")
            
        return "\n".join(lines)

    def render_workflows(self) -> str:
        if not self.briefing_data:
            return "No workflow data loaded."
            
        workflows = self.briefing_data.get("workflow_status", [])
        if not workflows:
            return "No active workflows."
            
        lines = []
        for wf in workflows:
            lines.append(
                f"  - State: {wf.get('state')} | Request: {wf.get('client_request_id')} | Project: {wf.get('project_id')}"
            )
        return "\n".join(lines)

    def render_attention_items(self) -> str:
        if not self.briefing_data:
            return "No attention items loaded."
            
        items = self.briefing_data.get("items_requiring_ceo_attention", [])
        if not items:
            return "No items require attention."
            
        lines = []
        for item in items:
            lines.append(f"  - [{item.get('type')}] {item.get('description')} (ID: {item.get('id') or 'N/A'})")
        return "\n".join(lines)

    def execute_command(self, command: str) -> str:
        if not command:
            return "Please enter a command."
            
        cmd_clean = command.strip().lower()
        
        if cmd_clean == "help":
            commands_list = [
                "Available commands:",
                "  help       - Show available commands",
                "  refresh    - Refresh daily briefing metrics",
                "  briefing   - Display daily briefing",
                "  projects   - Display active and completed projects",
                "  workers    - Display executive staff availability",
                "  workflows  - Display active workflows status",
                "  health     - Display operational health status",
                "  attention  - Display items requiring CEO attention",
                "  summary    - Display high-level organizational summary"
            ]
            return "\n".join(commands_list)
            
        elif cmd_clean == "refresh":
            self.refresh()
            return "Console refreshed."
            
        elif cmd_clean == "briefing":
            return self.render_briefing()
            
        elif cmd_clean == "projects":
            return self.render_projects()
            
        elif cmd_clean == "workers":
            if not self.briefing_data:
                return "No worker data loaded."
            avail = self.briefing_data.get("executive_availability", {})
            lines = [
                "Executive Availability:",
                f"  AVAILABLE: {avail.get('AVAILABLE', 0)}",
                f"  BUSY: {avail.get('BUSY', 0)}",
                f"  OFFLINE: {avail.get('OFFLINE', 0)}",
                f"  SUSPENDED: {avail.get('SUSPENDED', 0)}"
            ]
            return "\n".join(lines)
            
        elif cmd_clean == "workflows":
            return self.render_workflows()
            
        elif cmd_clean == "health":
            if not self.briefing_data:
                return "No health data loaded."
            return f"Operational Health: {self.briefing_data.get('operational_health', 'UNKNOWN')}"
            
        elif cmd_clean == "attention":
            return self.render_attention_items()
            
        elif cmd_clean == "summary":
            summary = self.briefing_engine.generate_summary()
            lines = [
                "Organizational Summary:",
                f"  Total Executives: {summary.get('total_executives', 0)}",
                f"  Available Executives: {summary.get('available_executives', 0)}",
                f"  Busy Executives: {summary.get('busy_executives', 0)}",
                f"  Projects: {summary.get('projects', 0)}",
                f"  Work Orders: {summary.get('work_orders', 0)}",
                f"  Deliverables: {summary.get('deliverables', 0)}",
                f"  Client Requests: {summary.get('client_requests', 0)}",
                f"  Operational Health: {summary.get('operational_health', 'UNKNOWN')}",
                f"  CEO Attention Items: {summary.get('ceo_attention_count', 0)}"
            ]
            return "\n".join(lines)
            
        else:
            return f"Unknown command: {command}"
