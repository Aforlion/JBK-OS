from __future__ import annotations

from typing import Any
import logging

LOGGER = logging.getLogger(__name__)


class KnowledgeRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, item: Any) -> Any:
        if item is None:
            raise ValueError("Knowledge item is required.")

        knowledge_id = getattr(item, "knowledge_id", None) or getattr(item, "id", None)
        if not knowledge_id:
            raise ValueError("Knowledge item must have a valid ID.")

        if knowledge_id in self._items:
            raise ValueError(f"Knowledge ID already registered: {knowledge_id}.")

        self._items[knowledge_id] = item
        LOGGER.info("object_id=%s action=register actor=system result=registered", knowledge_id)
        return item

    def unregister(self, knowledge_id: str) -> Any:
        if not knowledge_id:
            raise ValueError("Knowledge ID is required.")

        if knowledge_id not in self._items:
            raise ValueError(f"Knowledge ID is not registered: {knowledge_id}.")

        item = self._items.pop(knowledge_id)
        LOGGER.info("object_id=%s action=unregister actor=system result=unregistered", knowledge_id)
        return item

    def find_by_id(self, knowledge_id: str) -> Any | None:
        if not knowledge_id:
            raise ValueError("Knowledge ID is required.")
        return self._items.get(knowledge_id)

    def find_by_category(self, category: str) -> list[Any]:
        if not category:
            raise ValueError("Category is required.")

        cat_normalized = category.strip().lower()
        return [
            item
            for item in self._items.values()
            if getattr(item, "category", "").strip().lower() == cat_normalized
        ]

    def find_by_owner(self, owner: str) -> list[Any]:
        if not owner:
            raise ValueError("Owner is required.")

        owner_normalized = owner.strip().lower()
        return [
            item
            for item in self._items.values()
            if getattr(item, "owner", "").strip().lower() == owner_normalized
        ]

    def find_by_tag(self, tag: str) -> list[Any]:
        if not tag:
            raise ValueError("Tag is required.")

        tag_normalized = tag.strip().lower()
        matches = []
        for item in self._items.values():
            item_tags = getattr(item, "tags", [])
            if any(t.strip().lower() == tag_normalized for t in item_tags):
                matches.append(item)
        return matches

    def search(self, query: str) -> list[Any]:
        # BR-0026: Search operations are read-only
        if not query:
            return list(self._items.values())

        matches = []
        for item in self._items.values():
            if hasattr(item, "matches") and callable(item.matches):
                if item.matches(query):
                    matches.append(item)
            else:
                # Fallback simple search
                q = query.strip().lower()
                if (
                    q in getattr(item, "title", "").lower()
                    or q in getattr(item, "description", "").lower()
                ):
                    matches.append(item)
        return matches

    def list_items(self) -> list[Any]:
        return list(self._items.values())

    def summary(self) -> dict[str, Any]:
        items_by_status: dict[str, int] = {}
        items_by_category: dict[str, int] = {}

        for item in self._items.values():
            status = getattr(getattr(item, "status", None), "value", getattr(item, "status", "UNKNOWN"))
            items_by_status[status] = items_by_status.get(status, 0) + 1

            cat = getattr(item, "category", "UNKNOWN")
            items_by_category[cat] = items_by_category.get(cat, 0) + 1

        return {
            "total_registered_items": len(self._items),
            "items_by_status": items_by_status,
            "items_by_category": items_by_category,
        }

    def to_dict(self) -> dict[str, Any]:
        serialized_items = []
        for item in self._items.values():
            if hasattr(item, "to_dict") and callable(item.to_dict):
                serialized_items.append(item.to_dict())
            elif hasattr(item, "__dict__"):
                serialized_items.append(dict(item.__dict__))
            else:
                serialized_items.append(item)

        return {
            "items": serialized_items,
            "summary": self.summary(),
        }
