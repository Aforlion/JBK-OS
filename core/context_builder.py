from __future__ import annotations

from typing import Any

from core.work_order import WorkOrder
from core.project import Project
from core.knowledge_registry import KnowledgeRegistry


class ContextBuilder:
    """Automatically constructs execution context from organizational sources (BR-038-005)."""

    def build(
        self,
        work_order: WorkOrder,
        project: Project | None = None,
        knowledge_registry: KnowledgeRegistry | None = None,
        previous_deliverables: list[Any] | None = None,
        company_standards: list[str] | None = None,
    ) -> dict[str, Any]:
        """Assemble a structured context dictionary for prompt construction."""
        context: dict[str, Any] = {}

        # Work Order context (always present)
        context["work_order"] = {
            "id": work_order.id,
            "title": work_order.title,
            "objective": work_order.objective,
            "project_id": work_order.project_id,
        }

        # Project context
        if project:
            context["project"] = {
                "id": project.id,
                "title": project.title,
                "client": getattr(project, "client", "Unknown"),
                "description": getattr(project, "description", ""),
            }

        # Knowledge context
        if knowledge_registry:
            items = knowledge_registry.list_items()
            context["knowledge"] = [
                {"id": getattr(k, "id", getattr(k, "knowledge_id", "")), "title": getattr(k, "title", "")}
                for k in items[:5]  # Limit to 5 most relevant
            ]

        # Previous deliverables
        if previous_deliverables:
            context["previous_deliverables"] = [
                {"id": getattr(d, "id", ""), "title": getattr(d, "title", "")}
                for d in previous_deliverables[:5]
            ]

        # Company standards
        if company_standards:
            context["company_standards"] = list(company_standards)

        return context
