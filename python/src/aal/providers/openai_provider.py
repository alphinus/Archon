# AI Empire HQ - AAL OpenAI Provider
# Version: 1.0

import os
import time
from typing import Any, Dict, List, Literal, Optional

import openai

from ..interfaces import IAgentProvider
from ..models import AgentRequest, AgentResponse


class OpenAIProvider(IAgentProvider):
    """
    Concrete implementation of IAgentProvider for OpenAI models.
    """

    def __init__(self, model_configs: Dict[str, Dict[str, Any]]):
        super().__init__(model_configs)
        self._client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_name(self) -> str:
        return "openai"

    def get_capabilities(self) -> List[str]:
        all_capabilities = set()
        for model_config in self._model_configs.values():
            all_capabilities.update(model_config.get("capabilities", []))
        return list(all_capabilities)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.monotonic()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return self._create_error_response("OPENAI_API_KEY not configured.")

        if not self._client.api_key:
            self._client = openai.AsyncOpenAI(api_key=api_key) # Re-initialize if API key was missing earlier

        try:
            model_name_used = self._select_model(
                quality_tier=request.quality_tier,
                required_capabilities=request.required_capabilities
            )

            if not model_name_used:
                return self._create_error_response("No suitable OpenAI model found for request.")

            messages = self._format_messages(request.prompt, request.conversation_history)

            chat_completion = await self._client.chat.completions.create(
                model=model_name_used,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            end_time = time.monotonic()
            latency_ms = int((end_time - start_time) * 1000)

            content = chat_completion.choices[0].message.content or ""
            usage_data = chat_completion.usage.model_dump() if chat_completion.usage else {}

            cost_usd = self._calculate_cost(
                model_name_used, usage_data.get("prompt_tokens", 0), usage_data.get("completion_tokens", 0)
            )

            return AgentResponse(
                content=content,
                provider_used=self.get_name(),
                model_name_used=model_name_used,
                usage={"input_tokens": usage_data.get("prompt_tokens", 0), "output_tokens": usage_data.get("completion_tokens", 0)},
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )

        except Exception as e:
            end_time = time.monotonic()
            latency_ms = int((end_time - start_time) * 1000)
            return self._create_error_response(
                f"OpenAIProvider failed: {str(e)}", 
                latency_ms=latency_ms,
                model_name_used=model_name_used if 'model_name_used' in locals() else "none"
            )

    def _select_model(self, quality_tier: Literal["low", "medium", "high"], required_capabilities: List[str]) -> Optional[str]:
        """
        Selects the best OpenAI model based on quality tier and required capabilities.
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
        Formats the prompt and conversation history into OpenAI chat completion format.
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
        """
        Helper to create a standardized error response.
        """
        return AgentResponse(
            content="",
            provider_used=self.get_name(),
            model_name_used=model_name_used,
            usage={},
            cost_usd=0.0,
            latency_ms=latency_ms,
            error=error_message
        )
