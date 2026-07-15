from __future__ import annotations
from typing import Any
from datetime import datetime, timezone


class ConversationTurn:
    """Represents a single message exchange in an executive conversation session."""

    def __init__(
        self,
        turn_id: str,
        user_message: str,
        assistant_message: str,
        intent: str,
        confidence: float,
        engines_consulted: list[str],
        reasoning: str,
        execution_timeline: list[dict[str, Any]],
        created_at: str | None = None,
    ) -> None:
        self.turn_id = turn_id
        self.user_message = user_message
        self.assistant_message = assistant_message
        self.intent = intent
        self.confidence = confidence
        self.engines_consulted = list(engines_consulted or [])
        self.reasoning = reasoning
        self.execution_timeline = list(execution_timeline or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "intent": self.intent,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message,
            "assistant_message": self.assistant_message,
            "intent": self.intent,
            "confidence": self.confidence,
            "engines_consulted": list(self.engines_consulted),
            "reasoning": self.reasoning,
            "execution_timeline": list(self.execution_timeline),
            "created_at": self.created_at,
        }


class ExecutiveConversationRecord:
    """Ties together all turns within a session for organizational memory (BR-035-014)."""

    def __init__(
        self,
        session_id: str,
        executive_id: str,
        turns: list[ConversationTurn] | None = None,
        created_at: str | None = None,
    ) -> None:
        if not session_id:
            raise ValueError("Session ID is required.")
        if not executive_id:
            raise ValueError("Executive ID is required.")

        self.session_id = session_id
        self.executive_id = executive_id
        self.turns = list(turns or [])
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def add_turn(self, turn: ConversationTurn) -> None:
        self.turns.append(turn)

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "executive_id": self.executive_id,
            "turn_count": len(self.turns),
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "executive_id": self.executive_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "created_at": self.created_at,
        }
