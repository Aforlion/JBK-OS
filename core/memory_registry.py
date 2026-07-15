from __future__ import annotations

import logging
from typing import Any
from core.memory_record import MemoryRecord

LOGGER = logging.getLogger(__name__)

class MemoryRegistry:
    """Stores experienced memories and coordinates search, retrieval, merging, and archival."""

    def __init__(self) -> None:
        self._memories: dict[str, MemoryRecord] = {}

    def register(self, record: MemoryRecord) -> MemoryRecord:
        """Register a memory record. If a duplicate exists, merge them."""
        if not record:
            raise ValueError("Memory record is required.")

        # Duplicate checking: category + title
        for existing in self._memories.values():
            if (existing.category == record.category and 
                existing.title.strip().lower() == record.title.strip().lower() and 
                not existing.archived):
                
                # Merge duplicate
                LOGGER.info("object_id=%s action=merge actor=system result=merged_duplicate", existing.id)
                self._merge_records(existing, record)
                return existing

        self._memories[record.id] = record
        LOGGER.info("object_id=%s action=register actor=system result=registered", record.id)
        return record

    def _merge_records(self, existing: MemoryRecord, new_record: MemoryRecord) -> None:
        """Merge the contents of new_record into existing."""
        if new_record.full_context and new_record.full_context not in existing.full_context:
            existing.full_context += f"\n[Merged context]: {new_record.full_context}"
        
        # Merge summary if it is different
        if new_record.summary and new_record.summary not in existing.summary:
            existing.summary += f" | {new_record.summary}"

        # Union of related entities and tags
        existing.related_entities = sorted(list(set(existing.related_entities + new_record.related_entities)))
        existing.tags = sorted(list(set(existing.tags + new_record.tags)))
        
        # Take max values for importance and confidence
        existing.importance = max(existing.importance, new_record.importance)
        existing.confidence = max(existing.confidence, new_record.confidence)

    def search(self, query: str) -> list[MemoryRecord]:
        """Search active (non-archived) memories matching query."""
        if not query:
            return [m for m in self._memories.values() if not m.archived]
        return [m for m in self._memories.values() if not m.archived and m.matches(query)]

    def find_related(self, entity_id: str) -> list[MemoryRecord]:
        """Find active memories related to a specific entity ID."""
        if not entity_id:
            return []
        target = entity_id.strip().lower()
        return [
            m for m in self._memories.values() 
            if not m.archived and any(target in ent.strip().lower() for ent in m.related_entities)
        ]

    def find_recent(self, n: int = 10) -> list[MemoryRecord]:
        """Find recent active memories sorted by created_at descending."""
        active = [m for m in self._memories.values() if not m.archived]
        return sorted(active, key=lambda x: x.created_at or "", reverse=True)[:n]

    def find_by_client(self, client: str) -> list[MemoryRecord]:
        """Find active memories relating to a client."""
        if not client:
            return []
        c = client.strip().lower()
        return [
            m for m in self._memories.values()
            if not m.archived and (
                c in m.title.lower() or 
                c in m.summary.lower() or 
                any(c in tag.lower() for tag in m.tags) or 
                any(c in entity.lower() for entity in m.related_entities)
            )
        ]

    def find_by_project(self, project_id: str) -> list[MemoryRecord]:
        """Find active memories relating to a project ID."""
        return self.find_related(project_id)

    def find_by_tag(self, tag: str) -> list[MemoryRecord]:
        """Find active memories containing a specific tag."""
        if not tag:
            return []
        t = tag.strip().lower()
        return [
            m for m in self._memories.values() 
            if not m.archived and any(t == existing_tag.lower() for existing_tag in m.tags)
        ]

    def archive(self, memory_id: str) -> MemoryRecord:
        """Mark a memory record as archived (nothing is ever deleted)."""
        if memory_id not in self._memories:
            raise ValueError(f"Memory record not found: {memory_id}")
        record = self._memories[memory_id]
        record.archived = True
        LOGGER.info("object_id=%s action=archive actor=system result=archived", memory_id)
        return record

    def list_items(self) -> list[MemoryRecord]:
        """List all memories (including archived)."""
        return list(self._memories.values())

    def summarize(self) -> dict[str, Any]:
        """Summarize memory registry statistics."""
        categories: dict[str, int] = {}
        total_active = 0
        total_archived = 0
        confidences = []

        for m in self._memories.values():
            if m.archived:
                total_archived += 1
            else:
                total_active += 1
                categories[m.category] = categories.get(m.category, 0) + 1
                confidences.append(m.confidence)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_memories": len(self._memories),
            "active_memories": total_active,
            "archived_memories": total_archived,
            "categories": categories,
            "average_confidence": round(avg_conf, 2),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory registry to dict."""
        return {
            "memories": [m.to_dict() for m in self._memories.values()],
            "summary": self.summarize(),
        }
