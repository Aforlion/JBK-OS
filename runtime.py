from __future__ import annotations

from typing import Any


class Runtime:
    def __init__(
        self,
        config: dict[str, Any],
        company: dict[str, Any],
        worker_registry: Any,
        project_registry: Any,
        skill_registry: Any,
        knowledge_registry: Any,
        chief_of_staff: Any,
        execution_planner: Any,
        executive_briefing_engine: Any,
        execution_engine: Any,
        executive_console: Any,
        workspace_path: str,
        logging_config: dict[str, Any],
    ) -> None:
        self.config = config
        self.company = company
        self.worker_registry = worker_registry
        self.project_registry = project_registry
        self.skill_registry = skill_registry
        self.knowledge_registry = knowledge_registry
        self.chief_of_staff = chief_of_staff
        self.execution_planner = execution_planner
        self.executive_briefing_engine = executive_briefing_engine
        self.execution_engine = execution_engine
        self.executive_console = executive_console
        self.workspace_path = workspace_path
        self.logging_config = logging_config
        self.status = "READY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "company": self.company,
            "workspace_path": self.workspace_path,
        }
