from __future__ import annotations

import os
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class AIProviderStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"
    DEGRADED = "DEGRADED"


class AICapability(str, Enum):
    CHAT = "CHAT"
    REASONING = "REASONING"
    CODING = "CODING"
    RESEARCH = "RESEARCH"
    VISION = "VISION"
    OCR = "OCR"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    EMBEDDINGS = "EMBEDDINGS"
    SPEECH_TO_TEXT = "SPEECH_TO_TEXT"
    TEXT_TO_SPEECH = "TEXT_TO_SPEECH"


class AIProvider:
    """Represents an individual AI provider registration (BR-037-002)."""

    def __init__(
        self,
        provider_id: str,
        name: str,
        status: AIProviderStatus = AIProviderStatus.AVAILABLE,
        priority: int = 100,
        capabilities: list[AICapability] | None = None,
        supported_models: list[str] | None = None,
    ) -> None:
        if not provider_id:
            raise ValueError("Provider ID is required.")
        if not name:
            raise ValueError("Provider name is required.")

        self.provider_id = provider_id
        self.name = name
        self.status = status
        self.priority = priority
        self.capabilities = list(capabilities or [])
        self.supported_models = list(supported_models or [])

    def supports(self, capability: AICapability) -> bool:
        return capability in self.capabilities

    def is_available(self) -> bool:
        return self.status in (AIProviderStatus.AVAILABLE, AIProviderStatus.DEGRADED)

    def summary(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority,
            "capabilities": [c.value for c in self.capabilities],
            "supported_models": list(self.supported_models),
        }


# ---------------------------------------------------------------------------
# Abstract Adapter Interface
# ---------------------------------------------------------------------------


class AIProviderAdapter(ABC):
    """Abstract interface that every provider adapter must implement (BR-037-015)."""

    @abstractmethod
    def provider_id(self) -> str:
        """Return the unique provider identifier."""
        ...

    @abstractmethod
    def supports(self, capability: AICapability) -> bool:
        """Return True if this adapter can fulfil the given capability."""
        ...

    @abstractmethod
    def generate(self, request: Any) -> dict[str, Any]:
        """Execute an AI request and return a raw result dict."""
        ...

    @abstractmethod
    def health(self) -> AIProviderStatus:
        """Return the current health status of this provider."""
        ...

    @abstractmethod
    def models(self) -> list[str]:
        """Return the list of models supported by this provider."""
        ...


# ---------------------------------------------------------------------------
# Stub Adapters (Version 1 — simulated, no real API calls)
# ---------------------------------------------------------------------------

# Simple static pricing dictionary (per 1K tokens)
_MODEL_RATES: dict[str, float] = {
    "gemini-2.5-pro": 0.00125,
    "gemini-2.5-flash": 0.000075,
    "claude-opus-4": 0.015,
    "claude-sonnet-4": 0.003,
    "gpt-4.1": 0.002,
    "gpt-4.1-mini": 0.0004,
    "deepseek-r1": 0.00055,
    "llama-3.3-70b": 0.0,
}


class GeminiAdapter(AIProviderAdapter):
    """Stub adapter for Google Gemini (BR-037-002)."""

    CAPABILITIES = [
        AICapability.CHAT,
        AICapability.REASONING,
        AICapability.CODING,
        AICapability.RESEARCH,
        AICapability.VISION,
        AICapability.EMBEDDINGS,
    ]

    def __init__(self) -> None:
        self._api_key = os.environ.get("GEMINI_API_KEY", "")
        self._status = AIProviderStatus.AVAILABLE

    def provider_id(self) -> str:
        return "gemini"

    def supports(self, capability: AICapability) -> bool:
        return capability in self.CAPABILITIES

    def generate(self, request: Any) -> dict[str, Any]:
        start = time.monotonic()
        # Simulated response
        content = f"[Gemini] Simulated response for: {getattr(request, 'prompt', '')[:80]}"
        latency = int((time.monotonic() - start) * 1000)
        return {
            "content": content,
            "model": "gemini-2.5-pro",
            "token_usage": {"input": 50, "output": 120},
            "latency_ms": latency,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return self._status

    def models(self) -> list[str]:
        return ["gemini-2.5-pro", "gemini-2.5-flash"]


class ClaudeAdapter(AIProviderAdapter):
    """Stub adapter for Anthropic Claude (BR-037-002)."""

    CAPABILITIES = [
        AICapability.CHAT,
        AICapability.REASONING,
        AICapability.CODING,
        AICapability.RESEARCH,
        AICapability.VISION,
    ]

    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._status = AIProviderStatus.AVAILABLE

    def provider_id(self) -> str:
        return "claude"

    def supports(self, capability: AICapability) -> bool:
        return capability in self.CAPABILITIES

    def generate(self, request: Any) -> dict[str, Any]:
        start = time.monotonic()
        content = f"[Claude] Simulated response for: {getattr(request, 'prompt', '')[:80]}"
        latency = int((time.monotonic() - start) * 1000)
        return {
            "content": content,
            "model": "claude-opus-4",
            "token_usage": {"input": 55, "output": 130},
            "latency_ms": latency,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return self._status

    def models(self) -> list[str]:
        return ["claude-opus-4", "claude-sonnet-4"]


class OpenAIAdapter(AIProviderAdapter):
    """Stub adapter for OpenAI (BR-037-002)."""

    CAPABILITIES = [
        AICapability.CHAT,
        AICapability.REASONING,
        AICapability.CODING,
        AICapability.VISION,
        AICapability.IMAGE_GENERATION,
        AICapability.EMBEDDINGS,
        AICapability.SPEECH_TO_TEXT,
        AICapability.TEXT_TO_SPEECH,
    ]

    def __init__(self) -> None:
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        self._status = AIProviderStatus.AVAILABLE

    def provider_id(self) -> str:
        return "openai"

    def supports(self, capability: AICapability) -> bool:
        return capability in self.CAPABILITIES

    def generate(self, request: Any) -> dict[str, Any]:
        start = time.monotonic()
        content = f"[OpenAI] Simulated response for: {getattr(request, 'prompt', '')[:80]}"
        latency = int((time.monotonic() - start) * 1000)
        return {
            "content": content,
            "model": "gpt-4.1",
            "token_usage": {"input": 48, "output": 115},
            "latency_ms": latency,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return self._status

    def models(self) -> list[str]:
        return ["gpt-4.1", "gpt-4.1-mini"]


class OllamaAdapter(AIProviderAdapter):
    """Stub adapter for Ollama local models (BR-037-002)."""

    CAPABILITIES = [
        AICapability.CHAT,
        AICapability.CODING,
    ]

    def __init__(self) -> None:
        self._status = AIProviderStatus.AVAILABLE

    def provider_id(self) -> str:
        return "ollama"

    def supports(self, capability: AICapability) -> bool:
        return capability in self.CAPABILITIES

    def generate(self, request: Any) -> dict[str, Any]:
        start = time.monotonic()
        content = f"[Ollama] Simulated response for: {getattr(request, 'prompt', '')[:80]}"
        latency = int((time.monotonic() - start) * 1000)
        return {
            "content": content,
            "model": "llama-3.3-70b",
            "token_usage": {"input": 40, "output": 100},
            "latency_ms": latency,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return self._status

    def models(self) -> list[str]:
        return ["llama-3.3-70b"]
