# AI Empire HQ - Agent Abstraction Layer (AAL) Service
# Version: 1.1

from typing import Dict, List, Optional

from structlog import get_logger

from .circuit_breaker import get_circuit_breaker_registry
from .interfaces import IAgentProvider
from .metrics import MetricsCollector
from .models import AgentRequest, AgentResponse
from .registry import get_provider_registry

logger = get_logger(__name__)


class AgentService:
    """
    The central entry point for the Agent Abstraction Layer.

    This service holds a registry of all available agent providers and routes
    incoming requests to the appropriate provider.
    """

    def __init__(self, providers: List[IAgentProvider], enable_circuit_breaker: bool = True):
        """
        Initializes the service with a list of available providers.

        Args:
            providers: A list of concrete IAgentProvider implementations.
            enable_circuit_breaker: Whether to enable circuit breaker protection (default: True).
        """
        if not providers:
            raise ValueError("AgentService must be initialized with at least one provider.")

        self._providers: Dict[str, IAgentProvider] = {p.get_name(): p for p in providers}
        self._enable_circuit_breaker = enable_circuit_breaker
        self._circuit_breaker_registry = get_circuit_breaker_registry() if enable_circuit_breaker else None
        self._logger = logger.bind(service="AAL")
        self._logger.info(
            "agent_service_initialized",
            providers=list(self._providers.keys()),
            circuit_breaker_enabled=enable_circuit_breaker
        )

    async def execute_request(self, request: AgentRequest) -> AgentResponse:
        """
        Executes an agent request using advanced routing strategy.

        This router filters and sorts providers based on requested capabilities,
        quality tier, and cost, with a fallback mechanism.

        Args:
            request: The standardized agent request.

        Returns:
            The standardized agent response.
        """
        self._logger.info("agent_request_received", request=request.model_dump())
        candidate_providers: List[IAgentProvider] = []

        # 1. Filter providers based on preferred_provider (if specified)
        if request.preferred_provider:
            provider = self._providers.get(request.preferred_provider)
            if provider:
                candidate_providers.append(provider)
        else:
            candidate_providers = list(self._providers.values())

        if not candidate_providers:
            error_msg = "No AAL providers available."
            self._logger.error("agent_request_failed", error=error_msg)
            return self._create_error_response(error_msg)

        # 2. Further filter by required_capabilities
        if request.required_capabilities:
            filtered_by_capabilities = []
            for provider in candidate_providers:
                if all(cap in provider.get_capabilities() for cap in request.required_capabilities):
                    filtered_by_capabilities.append(provider)
            candidate_providers = filtered_by_capabilities

        if not candidate_providers:
            error_msg = "No AAL provider found with all required capabilities."
            self._logger.error("agent_request_failed", error=error_msg, required_capabilities=request.required_capabilities)
            return self._create_error_response(error_msg)

        # 3. Filter by max_cost_usd if specified
        if request.max_cost_usd is not None:
            cost_filtered_providers = []
            for provider in candidate_providers:
                # Estimate cost for this provider based on request
                estimated_cost = self._estimate_provider_cost(provider, request)
                if estimated_cost is not None and estimated_cost <= request.max_cost_usd:
                    cost_filtered_providers.append(provider)
                    self._logger.debug(
                        "provider_cost_check",
                        provider=provider.get_name(),
                        estimated_cost=estimated_cost,
                        max_budget=request.max_cost_usd,
                        accepted=True
                    )
                else:
                    self._logger.debug(
                        "provider_cost_check",
                        provider=provider.get_name(),
                        estimated_cost=estimated_cost,
                        max_budget=request.max_cost_usd,
                        accepted=False
                    )
            candidate_providers = cost_filtered_providers

        if not candidate_providers:
            error_msg = f"No AAL provider found within budget (max ${request.max_cost_usd})."
            self._logger.error("agent_request_failed", error=error_msg, max_cost_usd=request.max_cost_usd)
            return self._create_error_response(error_msg)

        # 4. Sort by quality (high > medium > low) and then by cost (cheapest first)
        # Note: Provider's _select_model already handles quality/cost per model.
        # Here we just sort providers based on their overall best model for the tier.
        # This is a simplified heuristic; a more advanced router might pre-calculate best models.
        def sort_key(provider: IAgentProvider):
            # Dummy cost/quality for provider. Actual model choice is within provider.execute.
            # We assume providers can generally handle tiers based on their advertised capabilities.
            if "quality_high" in provider.get_capabilities():
                return 3 # High quality
            if "quality_medium" in provider.get_capabilities():
                return 2 # Medium quality
            if "quality_low" in provider.get_capabilities():
                return 1 # Low quality
            return 0 # Unknown

        # Sort in descending order of quality (higher is better)
        candidate_providers.sort(key=sort_key, reverse=True)

        # 5. Execute with fallback and circuit breaker protection
        last_error: Optional[str] = None
        for provider in candidate_providers:
            provider_name = provider.get_name()

            # Check circuit breaker before attempting request
            if self._enable_circuit_breaker:
                circuit_breaker = self._circuit_breaker_registry.get_circuit_breaker(provider_name)
                if not circuit_breaker.is_request_allowed():
                    last_error = f"Provider {provider_name} circuit breaker is OPEN"
                    self._logger.warning(
                        "provider_circuit_open",
                        provider_name=provider_name,
                        circuit_state=circuit_breaker.state.value,
                        request_id=id(request)
                    )
                    continue  # Skip this provider, try next one

            self._logger.info("provider_attempt_started", provider_name=provider_name, request_id=id(request))
            try:
                response = await provider.execute(request)
                if not response.error:  # If provider execution was successful
                    # Record success with circuit breaker
                    if self._enable_circuit_breaker:
                        circuit_breaker.record_success()

                    # Record metrics
                    MetricsCollector.record_request(
                        provider=response.provider_used,
                        model=response.model_name_used,
                        quality_tier=request.quality_tier,
                        success=True
                    )
                    MetricsCollector.record_latency(
                        provider=response.provider_used,
                        model=response.model_name_used,
                        latency_seconds=response.latency_ms / 1000.0
                    )
                    MetricsCollector.record_cost(
                        provider=response.provider_used,
                        model=response.model_name_used,
                        cost_usd=response.cost_usd
                    )
                    if response.usage:
                        MetricsCollector.record_tokens(
                            provider=response.provider_used,
                            model=response.model_name_used,
                            input_tokens=response.usage.get("input_tokens", 0),
                            output_tokens=response.usage.get("output_tokens", 0)
                        )

                    self._logger.info(
                        "agent_response_sent",
                        provider_name=response.provider_used,
                        model_name=response.model_name_used,
                        cost_usd=response.cost_usd,
                        latency_ms=response.latency_ms,
                        input_tokens=response.usage.get("input_tokens"),
                        output_tokens=response.usage.get("output_tokens"),
                        request_id=id(request)
                    )
                    return response
                else:
                    # Record failure with circuit breaker
                    if self._enable_circuit_breaker:
                        circuit_breaker.record_failure()
                        MetricsCollector.record_circuit_breaker_failure(provider_name)

                    # Record failed request metrics
                    MetricsCollector.record_request(
                        provider=provider_name,
                        model=response.model_name_used if response.model_name_used != "none" else "unknown",
                        quality_tier=request.quality_tier,
                        success=False
                    )

                    last_error = f"Provider {provider_name} failed: {response.error}"
                    self._logger.warning("provider_attempt_failed", provider_name=provider_name, error=response.error, request_id=id(request))
            except Exception as e:
                # Record failure with circuit breaker
                if self._enable_circuit_breaker:
                    circuit_breaker = self._circuit_breaker_registry.get_circuit_breaker(provider_name)
                    circuit_breaker.record_failure()
                    MetricsCollector.record_circuit_breaker_failure(provider_name)

                # Record exception metrics
                MetricsCollector.record_request(
                    provider=provider_name,
                    model="unknown",
                    quality_tier=request.quality_tier,
                    success=False
                )

                last_error = f"Provider {provider_name} execution failed: {str(e)}"
                self._logger.exception("provider_attempt_failed", provider_name=provider_name, error=str(e), request_id=id(request))

        # All providers failed
        final_error_msg = f"All available AAL providers failed to execute the request. Last error: {last_error or 'None'}"
        self._logger.error("agent_request_failed", error=final_error_msg, request=request.model_dump())
        return self._create_error_response(final_error_msg, model_name_used="none")

    def _estimate_provider_cost(self, provider: IAgentProvider, request: AgentRequest) -> Optional[float]:
        """
        Estimate the cost for a provider to handle this request.

        Uses a simple heuristic based on average token usage and provider's model costs.
        This is a rough estimate; actual cost depends on the specific model selected.

        Args:
            provider: The provider to estimate cost for.
            request: The agent request containing prompt and parameters.

        Returns:
            Estimated cost in USD, or None if estimation is not possible.
        """
        if not hasattr(provider, '_model_configs'):
            return None

        # Rough token estimation: ~1 token per 4 characters
        estimated_input_tokens = len(request.prompt) // 4
        estimated_output_tokens = min(request.max_tokens, 1000)  # Conservative estimate

        # Find cheapest model for the quality tier
        quality_tier_map = {
            "low": "quality_low",
            "medium": "quality_medium",
            "high": "quality_high"
        }
        target_quality_cap = quality_tier_map.get(request.quality_tier, "quality_medium")

        cheapest_cost = None
        for model_name, model_config in provider._model_configs.items():
            capabilities = model_config.get("capabilities", [])
            if target_quality_cap in capabilities:
                cost_config = model_config.get("cost_per_million_tokens", {})
                input_cost_per_m = cost_config.get("input", 0)
                output_cost_per_m = cost_config.get("output", 0)

                estimated_cost = (
                    (estimated_input_tokens / 1_000_000) * input_cost_per_m +
                    (estimated_output_tokens / 1_000_000) * output_cost_per_m
                )

                if cheapest_cost is None or estimated_cost < cheapest_cost:
                    cheapest_cost = estimated_cost

        return cheapest_cost

    def _create_error_response(self, error_message: str, latency_ms: int = 0, model_name_used: str = "none") -> AgentResponse:
        """
        Helper to create a standardized error response.
        """
        return AgentResponse(
            content="",
            provider_used="aal_service",
            model_name_used=model_name_used,
            usage={},
            cost_usd=0.0,
            latency_ms=latency_ms,
            error=error_message
        )

def get_agent_service() -> AgentService:
    """
    Factory function to create an instance of the AgentService with
    all available providers, loaded dynamically from the ProviderRegistry.
    """
    registry = get_provider_registry()
    available_providers = registry.get_all_providers()
    if not available_providers:
        logger.warning("aal_no_providers_loaded", message="No AAL providers loaded. AgentService will be initialized with no providers.")
        # Initialize with an empty list of providers, the service will handle it gracefully
        return AgentService(providers=[])
    return AgentService(providers=available_providers)
