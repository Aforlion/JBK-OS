from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ProjectRegistry:
    def __init__(self) -> None:
        self._projects: dict[str, Any] = {}

    def register(self, project: Any) -> Any:
        project_id = self._get_project_id(project)
        if project_id in self._projects:
            raise ValueError(f"Project ID already registered: {project_id}.")

        self._projects[project_id] = project
        self._log_state_change(project_id, "register", "system", "registered")
        return project

    def unregister(self, project_id: str) -> Any:
        if not project_id:
            raise ValueError("Project ID is required.")
        if project_id not in self._projects:
            raise ValueError(f"Project ID is not registered: {project_id}.")

        project = self._projects.pop(project_id)
        self._log_state_change(project_id, "unregister", "system", "unregistered")
        return project

    def find_by_id(self, project_id: str) -> Any | None:
        if not project_id:
            raise ValueError("Project ID is required.")
        return self._projects.get(project_id)

    def list_projects(self) -> list[Any]:
        return list(self._projects.values())

    def list_by_status(self, status: Any) -> list[Any]:
        status_value = self._status_value(status)
        if not status_value:
            raise ValueError("Status is required.")

        return [
            project
            for project in self._projects.values()
            if self._status_value(getattr(project, "status", None)) == status_value
        ]

    def summary(self) -> dict[str, Any]:
        projects_by_status: dict[str, int] = {}

        for project in self._projects.values():
            status = self._status_value(getattr(project, "status", None)) or "UNKNOWN"
            projects_by_status[status] = projects_by_status.get(status, 0) + 1

        return {
            "total_projects": len(self._projects),
            "projects_by_status": projects_by_status,
            "active_projects": projects_by_status.get("ACTIVE", 0),
            "completed_projects": projects_by_status.get("COMPLETED", 0),
            "on_hold_projects": projects_by_status.get("ON_HOLD", 0),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "projects": [
                self._serialize_project(project)
                for project in self._projects.values()
            ],
            "summary": self.summary(),
        }

    @staticmethod
    def _get_project_id(project: Any) -> str:
        if project is None:
            raise ValueError("Project is required.")

        project_id = getattr(project, "id", None)
        if not project_id:
            raise ValueError("Project must have an ID.")
        return project_id

    @staticmethod
    def _status_value(status: Any) -> str | None:
        return getattr(status, "value", status)

    @staticmethod
    def _serialize_project(project: Any) -> Any:
        if hasattr(project, "to_dict") and callable(project.to_dict):
            return project.to_dict()
        if hasattr(project, "__dict__"):
            return dict(project.__dict__)
        return project

    @staticmethod
    def _log_state_change(
        project_id: str,
        action: str,
        actor: str,
        result: str,
    ) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            datetime.now(timezone.utc).isoformat(),
            project_id,
            action,
            actor,
            result,
        )
