from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

class MemoryRecord:
    """Represents a single experience memory within the JBK OS Organizational Memory."""

    def __init__(
        self,
        memory_id: str,
        category: str,
        title: str,
        summary: str,
        full_context: str,
        related_entities: list[str] | None = None,
        created_by: str = "system",
        created_at: str | None = None,
        confidence: float = 1.0,
        importance: int = 5,
        tags: list[str] | None = None,
        source_engine: str | None = None,
        archived: bool = False,
    ) -> None:
        self.id = memory_id
        self.category = category.strip().lower()
        self.title = title.strip()
        self.summary = summary.strip()
        self.full_context = full_context.strip()
        self.related_entities = related_entities or []
        self.created_by = created_by
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.confidence = float(confidence)
        self.importance = int(importance)
        self.tags = tags or []
        self.source_engine = source_engine
        self.archived = archived

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory record to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "full_context": self.full_context,
            "related_entities": self.related_entities,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "confidence": self.confidence,
            "importance": self.importance,
            "tags": self.tags,
            "source_engine": self.source_engine,
            "archived": self.archived,
        }

    def matches(self, query: str) -> bool:
        """Check if memory record matches the search query (case-insensitive keyword matching)."""
        if not query:
            return True
        q = query.strip().lower()
        if q in self.title.lower():
            return True
        if q in self.summary.lower():
            return True
        if q in self.full_context.lower():
            return True
        if any(q in tag.lower() for tag in self.tags):
            return True
        if any(q in entity.lower() for entity in self.related_entities):
            return True
        return False
