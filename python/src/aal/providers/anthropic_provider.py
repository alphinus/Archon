# AI Empire HQ - AAL Anthropic Claude Provider
# Version: 1.0

import os
import time
from typing import Any, Dict, List, Literal, Optional

from anthropic import Anthropic

from ..interfaces import IAgentProvider
from ..models import AgentRequest, AgentResponse


class ClaudeProvider(IAgentProvider):
    """
    Concrete implementation of IAgentProvider for Anthropic's Claude models.
    """

    def __init__(self, model_configs: Dict[str, Dict[str, Any]]):
        super().__init__(model_configs)
        self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def get_name(self) -> str:
        return "anthropic"

    def get_capabilities(self) -> List[str]:
        all_capabilities = set()
        for model_config in self._model_configs.values():
            all_capabilities.update(model_config.get("capabilities", []))
        return list(all_capabilities)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.monotonic()
        
        if not self._client.api_key:
            return self._create_error_response("ANTHROPIC_API_KEY not configured.")

        try:
            model_name_used = self._select_model(
                quality_tier=request.quality_tier,
                required_capabilities=request.required_capabilities
            )

            if not model_name_used:
                return self._create_error_response("No suitable Claude model found for request.")

            messages = self._format_messages(request.prompt, request.conversation_history)
            
            response_object = await self._client.messages.create(
                model=model_name_used,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=messages
            )

            end_time = time.monotonic()
            latency_ms = int((end_time - start_time) * 1000)
            
            content = response_object.content[0].text if response_object.content else ""
            
            # Anthropic API returns token usage in usage object
            usage_data = {
                "input_tokens": response_object.usage.input_tokens,
                "output_tokens": response_object.usage.output_tokens,
            } if response_object.usage else {}

            cost_usd = self._calculate_cost(
                model_name_used,
                usage_data.get("input_tokens", 0),
                usage_data.get("output_tokens", 0)
            )

            return AgentResponse(
                content=content,
                provider_used=self.get_name(),
                model_name_used=model_name_used,
                usage=usage_data,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )
        except Exception as e:
            end_time = time.monotonic()
            latency_ms = int((end_time - start_time) * 1000)
            return self._create_error_response(
                f"ClaudeProvider failed: {str(e)}", 
                latency_ms=latency_ms,
                model_name_used=model_name_used if 'model_name_used' in locals() else "none"
            )

    def _select_model(self, quality_tier: Literal["low", "medium", "high"], required_capabilities: List[str]) -> Optional[str]:
        """
        Selects the best Claude model based on quality tier and required capabilities.
        Prioritizes by quality and then by cost.
        """
        candidate_models = []
        for model_name, config in self._model_configs.items():
            model_capabilities = config.get("capabilities", [])
            model_quality = None
            for cap in model_capabilities:
                if cap.startswith("quality_"):
                    model_quality = cap.replace("quality_", "")
                    break

            # Filter by required capabilities
            if not all(cap in model_capabilities for cap in required_capabilities):
                continue
            
            # Filter by quality tier (simple match for now, could be hierarchical)
            if model_quality and (
                (quality_tier == "high" and model_quality != "high") or
                (quality_tier == "medium" and model_quality not in ["high", "medium"]) or
                (quality_tier == "low" and model_quality == "high")
            ):
                continue

            candidate_models.append({
                "name": model_name,
                "config": config,
                "cost_per_million_input_tokens": config.get("cost_per_million_tokens", {}).get("input", 0.0),
                "cost_per_million_output_tokens": config.get("cost_per_million_tokens", {}).get("output", 0.0),
                "quality": model_quality # for potential later advanced sorting
            })
        
        # Sort candidates: prioritize by quality (high > medium > low), then by cost (cheapest first)
        # This sorting logic can be further refined.
        quality_rank = {"high": 3, "medium": 2, "low": 1}
        candidate_models.sort(key=lambda x: (
            quality_rank.get(x["quality"], 0), 
            x["cost_per_million_input_tokens"] + x["cost_per_million_output_tokens"]
        ), reverse=True)

        return candidate_models[0]["name"] if candidate_models else None

    def _format_messages(self, prompt: str, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Formats the prompt and conversation history into Anthropic API format.
        """
        messages = []
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculates the cost based on the model's configured pricing.
        """
        model_pricing = self._model_configs.get(model, {}).get("cost_per_million_tokens", {})
        input_cost = model_pricing.get("input", 0.0)
        output_cost = model_pricing.get("output", 0.0)

        cost = (input_tokens / 1_000_000) * input_cost + \
               (output_tokens / 1_000_000) * output_cost
        return round(cost, 6)

    def _create_error_response(self, error_message: str, latency_ms: int = 0, model_name_used: str = "none") -> AgentResponse:
        """Helper to create a standardized error response."""
        return AgentResponse(
            content="",
            provider_used=self.get_name(),
            model_name_used=model_name_used,
            usage={},
            cost_usd=0.0,
            latency_ms=latency_ms,
            error=error_message
        )
