# AI Empire HQ - Agent Abstraction Layer (AAL) Interfaces
# Version: 1.0
# This file defines the abstract contracts that all AAL components must adhere to.

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .models import AgentRequest, AgentResponse


class IAgentProvider(ABC):
    """
    Abstract Base Class (Interface) for an AI Agent Provider.

    Each concrete provider (e.g., for OpenAI, Anthropic, Ollama) must implement
    this interface to be compatible with the Agent Abstraction Layer.
    """

    def __init__(self, model_configs: Dict[str, Dict[str, Any]]):
        """
        Initializes the provider with model-specific configurations.

        Args:
            model_configs: A dictionary containing configuration for various models
                           supported by this provider (e.g., capabilities, costs).
        """
        self._model_configs = model_configs

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the unique, lowercase name of the provider.
        e.g., "openai", "anthropic"
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Returns a list of capabilities this provider supports.
        e.g., ["text_generation", "code_generation", "tool_use"]
        """
        pass

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Executes the agent request.

        This method is responsible for:
        1. Translating the standardized AgentRequest into the provider-specific API format.
        2. Calling the provider's API.
        3. Translating the provider's response back into the standardized AgentResponse format.
        4. Calculating and populating observability data (latency, cost, token usage).

        Args:
            request: The standardized agent request object.

        Returns:
            A standardized agent response object.
        """
        pass
