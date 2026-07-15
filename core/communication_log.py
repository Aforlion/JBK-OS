from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class LogEntry:
    """A single immutable entry in the communication audit log."""

    def __init__(
        self,
        communication_id: str,
        action: str,
        timestamp: str | None = None,
        details: str = "",
    ) -> None:
        self.communication_id = communication_id
        self.action = action
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            "communication_id": self.communication_id,
            "action": self.action,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class CommunicationLog:
    """Permanent immutable audit log of every communication event.

    BR-045-002: Nothing is sent without an audit log.
    Entries are append-only. No mutation or deletion.
    """

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []

    def append(self, communication_id: str, action: str, details: str = "") -> LogEntry:
        """Append an immutable log entry."""
        entry = LogEntry(
            communication_id=communication_id,
            action=action,
            details=details,
        )
        self._entries.append(entry)
        return entry

    def search(self, query: str) -> list[LogEntry]:
        """Search log entries by communication_id, action, or details content."""
        query_lower = query.lower()
        return [
            e for e in self._entries
            if query_lower in e.communication_id.lower()
            or query_lower in e.action.lower()
            or query_lower in e.details.lower()
        ]

    def filter(
        self,
        communication_id: str | None = None,
        action: str | None = None,
    ) -> list[LogEntry]:
        """Filter log entries by exact communication_id and/or action."""
        results = self._entries
        if communication_id:
            results = [e for e in results if e.communication_id == communication_id]
        if action:
            results = [e for e in results if e.action == action]
        return results

    def summary(self) -> dict[str, Any]:
        """Summary statistics of the audit log."""
        actions: dict[str, int] = {}
        for entry in self._entries:
            actions[entry.action] = actions.get(entry.action, 0) + 1
        return {
            "total_entries": len(self._entries),
            "actions": actions,
        }

    def all_entries(self) -> list[LogEntry]:
        """Return all entries (read-only view)."""
        return list(self._entries)
