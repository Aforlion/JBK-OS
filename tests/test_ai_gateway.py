import unittest

from core.ai_provider import (
    AICapability,
    AIProvider,
    AIProviderAdapter,
    AIProviderStatus,
    GeminiAdapter,
    ClaudeAdapter,
    OpenAIAdapter,
    OllamaAdapter,
)
from core.ai_gateway import AIGateway, AIRequest, AIResponse
from core.ai_usage_record import AIUsageRecord


def _make_provider(pid: str, name: str, caps: list, priority: int = 100, status=AIProviderStatus.AVAILABLE) -> AIProvider:
    return AIProvider(provider_id=pid, name=name, capabilities=caps, priority=priority, status=status)


class _FailingAdapter(AIProviderAdapter):
    """Test double that always raises an exception."""

    def __init__(self, pid: str = "failing") -> None:
        self._pid = pid

    def provider_id(self) -> str:
        return self._pid

    def supports(self, capability: AICapability) -> bool:
        return True

    def generate(self, request) -> dict:
        raise RuntimeError("Simulated provider outage")

    def health(self) -> AIProviderStatus:
        return AIProviderStatus.AVAILABLE

    def models(self) -> list[str]:
        return ["fail-model"]


class _SuccessAdapter(AIProviderAdapter):
    """Test double that always succeeds."""

    def __init__(self, pid: str = "success") -> None:
        self._pid = pid

    def provider_id(self) -> str:
        return self._pid

    def supports(self, capability: AICapability) -> bool:
        return True

    def generate(self, request) -> dict:
        return {
            "content": f"[{self._pid}] OK",
            "model": "test-model",
            "token_usage": {"input": 10, "output": 20},
            "latency_ms": 1,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return AIProviderStatus.AVAILABLE

    def models(self) -> list[str]:
        return ["test-model"]


class TestAIGateway(unittest.TestCase):

    def setUp(self) -> None:
        self.gateway = AIGateway()

        # Register real stub adapters
        self.gemini = _make_provider("gemini", "Gemini", [AICapability.CHAT, AICapability.REASONING, AICapability.CODING], priority=10)
        self.claude = _make_provider("claude", "Claude", [AICapability.CHAT, AICapability.REASONING, AICapability.CODING], priority=20)
        self.openai = _make_provider("openai", "OpenAI", [AICapability.CHAT, AICapability.IMAGE_GENERATION], priority=30)
        self.ollama = _make_provider("ollama", "Ollama", [AICapability.CHAT, AICapability.CODING], priority=50)

        self.gateway.register_provider(self.gemini, GeminiAdapter())
        self.gateway.register_provider(self.claude, ClaudeAdapter())
        self.gateway.register_provider(self.openai, OpenAIAdapter())
        self.gateway.register_provider(self.ollama, OllamaAdapter())

    # ------------------------------------------------------------------
    # Provider Registration (BR-037-002)
    # ------------------------------------------------------------------

    def test_provider_registration(self) -> None:
        providers = self.gateway.list_providers()
        self.assertEqual(len(providers), 4)
        names = {p.name for p in providers}
        self.assertIn("Gemini", names)
        self.assertIn("Claude", names)
        self.assertIn("OpenAI", names)
        self.assertIn("Ollama", names)

    def test_provider_lookup(self) -> None:
        p = self.gateway.get_provider("gemini")
        self.assertIsNotNone(p)
        self.assertEqual(p.name, "Gemini")

        self.assertIsNone(self.gateway.get_provider("nonexistent"))

    # ------------------------------------------------------------------
    # Capability Matching (BR-037-003)
    # ------------------------------------------------------------------

    def test_capability_matching(self) -> None:
        # CHAT is supported by all 4
        candidates = self.gateway._find_compatible_providers(AICapability.CHAT)
        self.assertEqual(len(candidates), 4)

        # IMAGE_GENERATION only by OpenAI
        candidates = self.gateway._find_compatible_providers(AICapability.IMAGE_GENERATION)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].provider_id, "openai")

        # VIDEO_GENERATION by nobody
        candidates = self.gateway._find_compatible_providers(AICapability.VIDEO_GENERATION)
        self.assertEqual(len(candidates), 0)

    # ------------------------------------------------------------------
    # Routing Logic (BR-037-004)
    # ------------------------------------------------------------------

    def test_routing_selects_highest_priority(self) -> None:
        request = AIRequest(capability=AICapability.CHAT, prompt="Hello")
        response = self.gateway.generate(request)

        self.assertTrue(response.success)
        # Gemini has priority=10 (lowest value = highest priority)
        self.assertEqual(response.provider, "gemini")
        self.assertIn("Gemini", response.routing_reason)

    def test_routing_for_image_generation(self) -> None:
        request = AIRequest(capability=AICapability.IMAGE_GENERATION, prompt="Draw a logo")
        response = self.gateway.generate(request)

        self.assertTrue(response.success)
        self.assertEqual(response.provider, "openai")

    # ------------------------------------------------------------------
    # Fallback Execution (BR-037-005)
    # ------------------------------------------------------------------

    def test_fallback_on_provider_failure(self) -> None:
        # Replace gemini adapter with a failing one
        gw = AIGateway()
        p1 = _make_provider("primary", "Primary", [AICapability.CHAT], priority=1)
        p2 = _make_provider("backup", "Backup", [AICapability.CHAT], priority=2)

        gw.register_provider(p1, _FailingAdapter("primary"))
        gw.register_provider(p2, _SuccessAdapter("backup"))

        request = AIRequest(capability=AICapability.CHAT, prompt="Test fallback")
        response = gw.generate(request)

        self.assertTrue(response.success)
        self.assertEqual(response.provider, "backup")
        self.assertEqual(len(response.fallback_history), 1)
        self.assertEqual(response.fallback_history[0]["provider"], "primary")

    # ------------------------------------------------------------------
    # No Provider Available (BR-037-014)
    # ------------------------------------------------------------------

    def test_no_compatible_provider_returns_failure(self) -> None:
        request = AIRequest(capability=AICapability.VIDEO_GENERATION, prompt="Generate video")
        response = self.gateway.generate(request)

        self.assertFalse(response.success)
        self.assertEqual(response.provider, "none")
        self.assertIn("No compatible", response.content)

    def test_all_providers_fail_returns_failure(self) -> None:
        gw = AIGateway()
        p1 = _make_provider("fail1", "Fail1", [AICapability.CHAT], priority=1)
        p2 = _make_provider("fail2", "Fail2", [AICapability.CHAT], priority=2)

        gw.register_provider(p1, _FailingAdapter("fail1"))
        gw.register_provider(p2, _FailingAdapter("fail2"))

        request = AIRequest(capability=AICapability.CHAT, prompt="Test total failure")
        response = gw.generate(request)

        self.assertFalse(response.success)
        self.assertEqual(len(response.fallback_history), 2)

    # ------------------------------------------------------------------
    # Unavailable Provider Handling (BR-037-010)
    # ------------------------------------------------------------------

    def test_offline_provider_excluded_from_routing(self) -> None:
        self.gateway.update_provider_status("gemini", AIProviderStatus.OFFLINE)

        request = AIRequest(capability=AICapability.CHAT, prompt="Hello")
        response = self.gateway.generate(request)

        self.assertTrue(response.success)
        # Gemini is offline; Claude (priority=20) should be next
        self.assertEqual(response.provider, "claude")

    def test_disabled_provider_excluded(self) -> None:
        self.gateway.update_provider_status("gemini", AIProviderStatus.DISABLED)
        self.gateway.update_provider_status("claude", AIProviderStatus.DISABLED)

        request = AIRequest(capability=AICapability.REASONING, prompt="Think hard")
        response = self.gateway.generate(request)

        # Only Gemini and Claude had REASONING — both disabled, so failure
        self.assertFalse(response.success)

    def test_degraded_provider_still_available(self) -> None:
        self.gateway.update_provider_status("gemini", AIProviderStatus.DEGRADED)

        request = AIRequest(capability=AICapability.CHAT, prompt="Hello")
        response = self.gateway.generate(request)

        self.assertTrue(response.success)
        # Degraded is still available so Gemini should be selected
        self.assertEqual(response.provider, "gemini")

    # ------------------------------------------------------------------
    # Standardized Response (BR-037-007, BR-037-009)
    # ------------------------------------------------------------------

    def test_standardized_response_structure(self) -> None:
        request = AIRequest(capability=AICapability.CHAT, prompt="Test structure")
        response = self.gateway.generate(request)

        self.assertIsInstance(response, AIResponse)
        self.assertTrue(response.response_id.startswith("RES-"))
        self.assertEqual(response.request_id, request.request_id)
        self.assertIsInstance(response.provider, str)
        self.assertIsInstance(response.model, str)
        self.assertIsInstance(response.content, str)
        self.assertIsInstance(response.success, bool)
        self.assertIsInstance(response.latency_ms, int)
        self.assertIsInstance(response.token_usage, dict)
        self.assertIsInstance(response.estimated_cost, float)
        self.assertIsInstance(response.routing_reason, str)
        self.assertIsInstance(response.fallback_history, list)

    # ------------------------------------------------------------------
    # Usage Recording (BR-037-008)
    # ------------------------------------------------------------------

    def test_usage_recording(self) -> None:
        request = AIRequest(capability=AICapability.CHAT, prompt="Track me")
        self.gateway.generate(request)

        records = self.gateway.get_usage_records()
        self.assertEqual(len(records), 1)

        rec = records[0]
        self.assertIsInstance(rec, AIUsageRecord)
        self.assertEqual(rec.provider_id, "gemini")
        self.assertTrue(rec.success)
        self.assertGreaterEqual(rec.estimated_cost, 0.0)

    def test_multiple_requests_accumulate_usage(self) -> None:
        for _ in range(3):
            self.gateway.generate(AIRequest(capability=AICapability.CHAT, prompt="Hello"))
        self.assertEqual(len(self.gateway.get_usage_records()), 3)

    # ------------------------------------------------------------------
    # Provider Health Changes (BR-037-010)
    # ------------------------------------------------------------------

    def test_provider_health_update(self) -> None:
        self.gateway.update_provider_status("gemini", AIProviderStatus.OFFLINE)
        p = self.gateway.get_provider("gemini")
        self.assertEqual(p.status, AIProviderStatus.OFFLINE)

    def test_invalid_provider_health_update_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.gateway.update_provider_status("nonexistent", AIProviderStatus.OFFLINE)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_provider_serialization(self) -> None:
        p = self.gateway.get_provider("gemini")
        d = p.to_dict()
        self.assertEqual(d["provider_id"], "gemini")
        self.assertIn("CHAT", d["capabilities"])

        s = p.summary()
        self.assertEqual(s["name"], "Gemini")

    def test_usage_record_serialization(self) -> None:
        self.gateway.generate(AIRequest(capability=AICapability.CHAT, prompt="Serialize"))
        rec = self.gateway.get_usage_records()[0]

        d = rec.to_dict()
        self.assertIn("record_id", d)
        self.assertIn("provider_id", d)
        self.assertIn("estimated_cost", d)

        s = rec.summary()
        self.assertIn("model", s)

    # ------------------------------------------------------------------
    # Adapter Interface Compliance
    # ------------------------------------------------------------------

    def test_adapter_interface_compliance(self) -> None:
        for AdapterClass in [GeminiAdapter, ClaudeAdapter, OpenAIAdapter, OllamaAdapter]:
            adapter = AdapterClass()
            self.assertIsInstance(adapter.provider_id(), str)
            self.assertIsInstance(adapter.health(), AIProviderStatus)
            self.assertIsInstance(adapter.models(), list)
            self.assertGreater(len(adapter.models()), 0)
            # Verify supports returns bool
            self.assertIsInstance(adapter.supports(AICapability.CHAT), bool)

    # ------------------------------------------------------------------
    # Multiple Providers for Same Capability
    # ------------------------------------------------------------------

    def test_multiple_providers_same_capability(self) -> None:
        # CODING is supported by Gemini (10), Claude (20), Ollama (50)
        candidates = self.gateway._find_compatible_providers(AICapability.CODING)
        self.assertEqual(len(candidates), 3)
        # Verify priority ordering
        self.assertEqual(candidates[0].provider_id, "gemini")
        self.assertEqual(candidates[1].provider_id, "claude")
        self.assertEqual(candidates[2].provider_id, "ollama")


if __name__ == "__main__":
    unittest.main()
