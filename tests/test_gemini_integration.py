import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure JBK-OS modules are discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.ai_provider import GeminiAdapter, AICapability, AIProviderStatus
from core.ai_gateway import AIRequest, AIGateway
from core.prompt_manager import PromptManager


class TestGeminiIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.adapter = GeminiAdapter()
        self.request = AIRequest(
            capability=AICapability.CHAT,
            prompt="Hello Gemini",
            system_context="You are a helper.",
            temperature=0.5,
            max_tokens=1000
        )

    def test_adapter_basics(self) -> None:
        self.assertEqual(self.adapter.provider_id(), "gemini")
        self.assertTrue(self.adapter.supports(AICapability.CHAT))
        self.assertTrue(self.adapter.supports(AICapability.CODING))
        self.assertFalse(self.adapter.supports(AICapability.IMAGE_GENERATION))
        self.assertEqual(self.adapter.health(), AIProviderStatus.AVAILABLE)
        self.assertIn("gemini-2.5-flash", self.adapter.models())

    def test_generate_simulated_without_key(self) -> None:
        """Verifies simulated fallback occurs when no environment API key is present."""
        with patch.dict(os.environ, {}, clear=True):
            res = self.adapter.generate(self.request)
            self.assertTrue(res["success"])
            self.assertIn("Gemini Simulator", res["content"])
            self.assertEqual(res["model"], "gemini-2.5-flash")
            self.assertGreaterEqual(res["latency_ms"], 0)

    def test_successful_generate_with_mocked_client(self) -> None:
        """Verifies correct types and mappings mapped from google-genai Client."""
        # Setup mocks and isolate sys.modules to mock import google.genai
        mock_response = MagicMock()
        mock_response.text = "Hello back from Gemini"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20

        # Build nested mock client structure
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        # Mock the entire google.genai module structure
        mock_genai_mod = MagicMock()
        mock_genai_mod.genai.Client.return_value = mock_client
        mock_genai_mod.Client.return_value = mock_client
        
        # Ensure imports work and Client(api_key) instantiation is captured correctly
        with patch.dict("sys.modules", {
            "google": mock_genai_mod,
            "google.genai": mock_genai_mod,
            "google.genai.types": mock_genai_mod.types,
            "google.genai.errors": mock_genai_mod.errors
        }):


            with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"}):
                res = self.adapter.generate(self.request)
                self.assertTrue(res["success"])
                self.assertEqual(res["content"], "Hello back from Gemini")
                self.assertEqual(res["token_usage"]["input"], 10)
                self.assertEqual(res["token_usage"]["output"], 20)



    def test_prompt_manager_rendering(self) -> None:
        """Verifies PromptManager rendering and metadata mapping."""
        # Create temp prompt configuration path
        prompts_yaml = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "system_prompts.yaml")
        pm = PromptManager(prompts_yaml)

        # Check metadata
        meta = pm.get_prompt_metadata("coding_assistant")
        self.assertEqual(meta["version"], "1.0.0")
        self.assertEqual(meta["owner"], "CTO")

        # Check rendering
        rendered = pm.render("coding_assistant", task_description="Implement auth logic")
        self.assertIn("Implement auth logic", rendered)
        self.assertIn("You are the JBK OS Senior Software Engineer", rendered)


if __name__ == "__main__":
    unittest.main()
