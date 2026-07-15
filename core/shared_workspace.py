from __future__ import annotations

from typing import Any


class SharedWorkspace:
    """An isolation boundary enabling participants to exchange artifacts (BR-039-005)."""

    def __init__(self) -> None:
        self._artifacts: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        """Store an artifact in the workspace."""
        self._artifacts[key] = value

    def get(self, key: str) -> Any | None:
        """Retrieve an artifact from the workspace."""
        return self._artifacts.get(key)

    def list_keys(self) -> list[str]:
        """List all artifact keys currently stored in the workspace."""
        return list(self._artifacts.keys())

    def clear(self) -> None:
        """Clear the workspace."""
        self._artifacts.clear()

    def to_dict(self) -> dict[str, Any]:
        serialized = {}
        for k, v in self._artifacts.items():
            if hasattr(v, "to_dict"):
                serialized[k] = v.to_dict()
            elif hasattr(v, "summary"):
                serialized[k] = v.summary()
            else:
                serialized[k] = str(v)
        return serialized
