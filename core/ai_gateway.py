from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from core.ai_provider import (
    AICapability,
    AIProvider,
    AIProviderAdapter,
    AIProviderStatus,
    _MODEL_RATES,
)
from core.ai_usage_record import AIUsageRecord

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardized Request / Response Models
# ---------------------------------------------------------------------------


@dataclass
class AIRequest:
    """Standardized request object for all AI interactions (BR-037-006)."""

    capability: AICapability
    prompt: str
    request_id: str = ""
    system_context: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"


@dataclass
class AIResponse:
    """Standardized response object returned by the AI Gateway (BR-037-007, BR-037-009)."""

    response_id: str
    request_id: str
    provider: str
    model: str
    content: str
    success: bool
    latency_ms: int
    token_usage: dict[str, int]
    estimated_cost: float
    routing_reason: str
    fallback_history: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AI Gateway
# ---------------------------------------------------------------------------


class AIGateway:
    """Unified intelligence layer for JBK-OS (Spec 037).

    All AI interactions pass through this gateway which handles provider
    discovery, capability matching, routing, fallback, usage tracking,
    and standardized responses.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._adapters: dict[str, AIProviderAdapter] = {}
        self._usage_records: list[AIUsageRecord] = []
        self._usage_counter = 1

    # ------------------------------------------------------------------
    # Provider Management (BR-037-002)
    # ------------------------------------------------------------------

    def register_provider(
        self, provider: AIProvider, adapter: AIProviderAdapter
    ) -> None:
        """Register a provider and its adapter with the gateway."""
        if provider is None:
            raise ValueError("AIProvider is required.")
        if adapter is None:
            raise ValueError("AIProviderAdapter is required.")
        self._providers[provider.provider_id] = provider
        self._adapters[provider.provider_id] = adapter
        LOGGER.info(
            "object_id=%s action=register_provider actor=system result=registered",
            provider.provider_id,
        )

    def get_provider(self, provider_id: str) -> AIProvider | None:
        return self._providers.get(provider_id)

    def list_providers(self) -> list[AIProvider]:
        return list(self._providers.values())

    def update_provider_status(
        self, provider_id: str, status: AIProviderStatus
    ) -> None:
        """Update the health state of a provider (BR-037-010)."""
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ValueError(f"Provider {provider_id} not found.")
        provider.status = status
        LOGGER.info(
            "object_id=%s action=update_status actor=system result=%s",
            provider_id,
            status.value,
        )

    # ------------------------------------------------------------------
    # Core Generation (BR-037-004, BR-037-005, BR-037-014)
    # ------------------------------------------------------------------

    def generate(self, request: AIRequest) -> AIResponse:
        """Route an AI request to the best available provider with fallback."""
        if request is None:
            raise ValueError("AIRequest is required.")

        # 1. Discover compatible providers sorted by priority (lower = higher priority)
        candidates = self._find_compatible_providers(request.capability)

        if not candidates:
            # BR-037-014: Graceful failure
            return AIResponse(
                response_id=f"RES-{uuid.uuid4().hex[:8].upper()}",
                request_id=request.request_id,
                provider="none",
                model="none",
                content="No compatible AI provider is available for the requested capability.",
                success=False,
                latency_ms=0,
                token_usage={},
                estimated_cost=0.0,
                routing_reason=f"No provider supports capability '{request.capability.value}'.",
                fallback_history=[],
            )

        # 2. Attempt providers in priority order with fallback (BR-037-005)
        fallback_history: list[dict[str, str]] = []
        last_error = ""

        for provider in candidates:
            adapter = self._adapters.get(provider.provider_id)
            if adapter is None:
                continue

            try:
                raw = adapter.generate(request)
                if not raw.get("success", False):
                    fallback_history.append(
                        {
                            "provider": provider.provider_id,
                            "reason": "Adapter returned success=False.",
                        }
                    )
                    continue

                # Success path
                model = raw.get("model", "unknown")
                token_usage = raw.get("token_usage", {})
                latency_ms = raw.get("latency_ms", 0)
                estimated_cost = self._estimate_cost(model, token_usage)

                response = AIResponse(
                    response_id=f"RES-{uuid.uuid4().hex[:8].upper()}",
                    request_id=request.request_id,
                    provider=provider.provider_id,
                    model=model,
                    content=raw.get("content", ""),
                    success=True,
                    latency_ms=latency_ms,
                    token_usage=token_usage,
                    estimated_cost=estimated_cost,
                    routing_reason=f"Selected '{provider.name}' (priority={provider.priority}) for capability '{request.capability.value}'.",
                    fallback_history=fallback_history,
                )

                # Record usage (BR-037-008)
                self._record_usage(request, response)
                return response

            except Exception as exc:
                last_error = str(exc)
                fallback_history.append(
                    {
                        "provider": provider.provider_id,
                        "reason": f"Exception: {last_error}",
                    }
                )
                continue

        # All providers exhausted — graceful failure (BR-037-014)
        failure_response = AIResponse(
            response_id=f"RES-{uuid.uuid4().hex[:8].upper()}",
            request_id=request.request_id,
            provider="none",
            model="none",
            content=f"All compatible providers failed. Last error: {last_error}",
            success=False,
            latency_ms=0,
            token_usage={},
            estimated_cost=0.0,
            routing_reason="All fallback providers exhausted.",
            fallback_history=fallback_history,
        )
        self._record_usage(request, failure_response)
        return failure_response

    # ------------------------------------------------------------------
    # Usage Tracking (BR-037-008)
    # ------------------------------------------------------------------

    def get_usage_records(self) -> list[AIUsageRecord]:
        return list(self._usage_records)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _find_compatible_providers(
        self, capability: AICapability
    ) -> list[AIProvider]:
        """Return providers that support the capability and are healthy, sorted by priority."""
        compatible = [
            p
            for p in self._providers.values()
            if p.supports(capability) and p.is_available()
        ]
        compatible.sort(key=lambda p: p.priority)
        return compatible

    def _estimate_cost(
        self, model: str, token_usage: dict[str, int]
    ) -> float:
        rate = _MODEL_RATES.get(model, 0.001)
        total_tokens = token_usage.get("input", 0) + token_usage.get("output", 0)
        return round(rate * (total_tokens / 1000), 6)

    def _record_usage(self, request: AIRequest, response: AIResponse) -> None:
        record_id = f"USG-{self._usage_counter:04d}"
        self._usage_counter += 1
        record = AIUsageRecord(
            record_id=record_id,
            request_id=request.request_id,
            provider_id=response.provider,
            model=response.model,
            latency_ms=response.latency_ms,
            token_usage=response.token_usage,
            estimated_cost=response.estimated_cost,
            success=response.success,
        )
        self._usage_records.append(record)
