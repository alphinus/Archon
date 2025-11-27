# AI Empire HQ - Agent Abstraction Layer (AAL) Service
# Version: 1.0

from typing import Dict, List, Optional

from structlog import get_logger  # Import structlog logger

from .interfaces import IAgentProvider
from .models import AgentRequest, AgentResponse
from .registry import get_provider_registry

logger = get_logger(__name__)


class AgentService:
    """
    The central entry point for the Agent Abstraction Layer.

    This service holds a registry of all available agent providers and routes
    incoming requests to the appropriate provider.
    """

    def __init__(self, providers: List[IAgentProvider]):
        """
        Initializes the service with a list of available providers.

        Args:
            providers: A list of concrete IAgentProvider implementations.
        """
        if not providers:
            raise ValueError("AgentService must be initialized with at least one provider.")
        
        self._providers: Dict[str, IAgentProvider] = {p.get_name(): p for p in providers}
        self._logger = logger.bind(service="AAL")
        self._logger.info("agent_service_initialized", providers=list(self._providers.keys()))

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

        # 3. Sort by quality (high > medium > low) and then by cost (cheapest first)
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

        # 4. Execute with fallback
        last_error: Optional[str] = None
        for provider in candidate_providers:
            self._logger.info("provider_attempt_started", provider_name=provider.get_name(), request_id=id(request))
            try:
                response = await provider.execute(request)
                if not response.error: # If provider execution was successful
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
                    last_error = f"Provider {provider.get_name()} failed: {response.error}"
                    self._logger.warning("provider_attempt_failed", provider_name=provider.get_name(), error=response.error, request_id=id(request))
            except Exception as e:
                last_error = f"Provider {provider.get_name()} execution failed: {str(e)}"
                self._logger.exception("provider_attempt_failed", provider_name=provider.get_name(), error=str(e), request_id=id(request))

        # All providers failed
        final_error_msg = f"All available AAL providers failed to execute the request. Last error: {last_error or 'None'}"
        self._logger.error("agent_request_failed", error=final_error_msg, request=request.model_dump())
        return self._create_error_response(final_error_msg, model_name_used="none")

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
