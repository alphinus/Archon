"""Tests for AAL Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aal.service import AgentService
from aal.models import AgentRequest, AgentResponse
from aal.interfaces import IAgentProvider


class MockProvider(IAgentProvider):
    """Mock provider for testing"""

    def __init__(self, name: str, capabilities: list[str], should_fail: bool = False):
        super().__init__(model_configs={})
        self._name = name
        self._capabilities = capabilities
        self._should_fail = should_fail
        self.call_count = 0

    def get_name(self) -> str:
        return self._name

    def get_capabilities(self) -> list[str]:
        return self._capabilities

    async def execute(self, request: AgentRequest) -> AgentResponse:
        self.call_count += 1

        if self._should_fail:
            return AgentResponse(
                content="",
                provider_used=self._name,
                model_name_used="test-model",
                usage={},
                cost_usd=0.0,
                latency_ms=100,
                error="Mock failure"
            )

        return AgentResponse(
            content="Test response",
            provider_used=self._name,
            model_name_used="test-model",
            usage={"input_tokens": 10, "output_tokens": 20},
            cost_usd=0.001,
            latency_ms=100
        )


@pytest.mark.asyncio
class TestAgentService:
    """Test Agent Service functionality"""

    async def test_executes_preferred_provider(self):
        """Service should use preferred provider when specified"""
        provider1 = MockProvider("provider1", ["text_generation"])
        provider2 = MockProvider("provider2", ["text_generation"])

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        request = AgentRequest(
            prompt="Test",
            preferred_provider="provider2"
        )

        response = await service.execute_request(request)

        assert response.provider_used == "provider2"
        assert provider2.call_count == 1
        assert provider1.call_count == 0

    async def test_filters_by_capabilities(self):
        """Service should filter providers by required capabilities"""
        provider1 = MockProvider("provider1", ["text_generation"])
        provider2 = MockProvider("provider2", ["text_generation", "code_generation"])

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        request = AgentRequest(
            prompt="Test",
            required_capabilities=["code_generation"]
        )

        response = await service.execute_request(request)

        assert response.provider_used == "provider2"
        assert provider2.call_count == 1
        assert provider1.call_count == 0

    async def test_fallback_on_provider_failure(self):
        """Service should try next provider if first one fails"""
        provider1 = MockProvider("provider1", ["text_generation"], should_fail=True)
        provider2 = MockProvider("provider2", ["text_generation"])

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        request = AgentRequest(prompt="Test")

        response = await service.execute_request(request)

        assert response.provider_used == "provider2"
        assert provider1.call_count == 1
        assert provider2.call_count == 1

    async def test_returns_error_when_all_providers_fail(self):
        """Service should return error response when all providers fail"""
        provider1 = MockProvider("provider1", ["text_generation"], should_fail=True)
        provider2 = MockProvider("provider2", ["text_generation"], should_fail=True)

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        request = AgentRequest(prompt="Test")

        response = await service.execute_request(request)

        assert response.error is not None
        assert "failed" in response.error.lower()
        assert provider1.call_count == 1
        assert provider2.call_count == 1

    async def test_returns_error_when_no_capabilities_match(self):
        """Service should return error when no provider has required capabilities"""
        provider1 = MockProvider("provider1", ["text_generation"])
        provider2 = MockProvider("provider2", ["text_generation"])

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        request = AgentRequest(
            prompt="Test",
            required_capabilities=["quantum_computing"]
        )

        response = await service.execute_request(request)

        assert response.error is not None
        assert "capabilities" in response.error.lower()
        assert provider1.call_count == 0
        assert provider2.call_count == 0

    async def test_cost_estimation_and_filtering(self):
        """Service should filter providers by cost when max_cost_usd is set"""
        # Create providers with model configs for cost estimation
        provider1 = MockProvider("provider1", ["text_generation", "quality_high"])
        provider1._model_configs = {
            "expensive-model": {
                "capabilities": ["quality_high"],
                "cost_per_million_tokens": {"input": 100.0, "output": 200.0}
            }
        }

        provider2 = MockProvider("provider2", ["text_generation", "quality_medium"])
        provider2._model_configs = {
            "cheap-model": {
                "capabilities": ["quality_medium"],
                "cost_per_million_tokens": {"input": 1.0, "output": 2.0}
            }
        }

        service = AgentService([provider1, provider2], enable_circuit_breaker=False)

        # Request with very low budget should filter out expensive provider
        request = AgentRequest(
            prompt="Test prompt that needs processing",
            max_cost_usd=0.0001,
            quality_tier="medium"
        )

        response = await service.execute_request(request)

        # Should use cheap provider
        assert response.provider_used == "provider2"
        assert provider2.call_count == 1
        # Expensive provider should be filtered out by cost
        assert provider1.call_count == 0

    async def test_circuit_breaker_integration(self):
        """Service should respect circuit breaker state"""
        provider1 = MockProvider("provider1", ["text_generation"], should_fail=True)
        provider2 = MockProvider("provider2", ["text_generation"])

        service = AgentService([provider1, provider2], enable_circuit_breaker=True)

        # Make enough failed requests to open circuit breaker (default threshold: 5)
        for _ in range(5):
            request = AgentRequest(prompt="Test", preferred_provider="provider1")
            await service.execute_request(request)

        # Next request should skip provider1 due to open circuit
        request = AgentRequest(prompt="Test")
        response = await service.execute_request(request)

        # Should use provider2 directly without trying provider1
        assert response.provider_used == "provider2"
        # provider1 should have been called 5 times (to open circuit), but not on 6th request
        assert provider1.call_count == 5
