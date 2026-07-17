import unittest
from fastapi.testclient import TestClient

from bootstrap import bootstrap
from core.ai_gateway import AIGateway, AIRequest, AICapability
from core.ai_provider import AIProvider, AIProviderAdapter
from core.monitoring_engine import MonitoringEngine
from core.executive_console_controller import ExecutiveConsoleController
from web.app import create_app


class MockAdapter(AIProviderAdapter):
    def provider_id(self) -> str:
        return "mock-provider"
    
    def supports(self, capability: AICapability) -> bool:
        return capability == AICapability.CHAT
        
    def health(self):
        from core.ai_provider import AIProviderStatus
        return AIProviderStatus.AVAILABLE
        
    def models(self) -> list[str]:
        return ["gemini-1.5-pro"]

    def generate(self, request: AIRequest) -> dict:
        return {
            "success": True,
            "content": "Mocked response",
            "model": "gemini-1.5-pro",
            "latency_ms": 150,
            "token_usage": {"input": 10, "output": 20}
        }


class TestTelemetryInstrumentation(unittest.TestCase):

    def test_bootstrap_initializes_monitoring_engine(self) -> None:
        runtime = bootstrap()
        self.assertIsNotNone(runtime.monitoring_engine)
        self.assertIsInstance(runtime.monitoring_engine, MonitoringEngine)

    def test_ai_gateway_records_metrics(self) -> None:
        monitoring_engine = MonitoringEngine()
        gateway = AIGateway(monitoring_engine=monitoring_engine)
        
        provider = AIProvider(
            provider_id="mock-provider",
            name="Mock Provider",
            capabilities=[AICapability.CHAT],
            priority=1,
        )
        adapter = MockAdapter()
        gateway.register_provider(provider, adapter)
        
        request = AIRequest(capability=AICapability.CHAT, prompt="Hello")
        response = gateway.generate(request)
        
        self.assertTrue(response.success)
        metrics = monitoring_engine.list_metrics()
        
        # Verify AIGateway logged its metric
        ai_metrics = [m for m in metrics if m.engine_name == "AIGateway"]
        self.assertEqual(len(ai_metrics), 1)
        self.assertEqual(ai_metrics[0].execution_time_ms, 150.0)
        self.assertEqual(ai_metrics[0].ai_tokens, 30)

    def test_web_middleware_and_metrics_endpoint(self) -> None:
        monitoring_engine = MonitoringEngine()
        controller = ExecutiveConsoleController(monitoring_engine=monitoring_engine)
        app = create_app(controller)
        client = TestClient(app)
        
        # Call a route that doesn't exist to generate a request (will be 404, but not 500 so success=True)
        client.get("/api/dashboard/some-nonexistent-endpoint")
        
        # Verify WebServer metric was recorded
        metrics = monitoring_engine.list_metrics()
        web_metrics = [m for m in metrics if m.engine_name == "WebServer"]
        self.assertEqual(len(web_metrics), 1)
        self.assertTrue(web_metrics[0].success)
        
        # Verify retrieving metrics endpoint
        # Seed AI usage metric as well
        monitoring_engine.record_metric(
            engine_name="AIGateway",
            execution_time_ms=250.0,
            ai_tokens=100,
            ai_cost=0.002,
            success=True
        )
        
        response = client.get("/api/dashboard/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("average_response_time_ms", data)
        self.assertEqual(data["ai_latency_ms"], 250.0)
        self.assertEqual(data["requests_per_day"], 1)
        self.assertEqual(data["token_usage"], 100)
        self.assertEqual(data["estimated_ai_cost"], 0.002)
        self.assertEqual(data["error_rate_pct"], 0.0)
