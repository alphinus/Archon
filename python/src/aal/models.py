# AI Empire HQ - Agent Abstraction Layer (AAL) Data Models
# Version: 1.0
# This file defines the standardized communication protocol for interacting with the AAL.

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """
    Standardized request sent to the Agent Abstraction Layer.
    This model decouples the calling service from the specifics of any single AI provider.
    """

    prompt: str = Field(
        ...,
        description="The primary prompt or question for the AI agent."
    )
    conversation_history: List[dict[str, Any]] = Field(
        default_factory=list,
        description="A list of previous messages for maintaining conversational context."
    )

    # --- Routing Preferences ---
    preferred_provider: Optional[str] = Field(
        default=None,
        description="Explicitly request a specific provider (e.g., 'anthropic', 'openai')."
    )
    required_capabilities: List[str] = Field(
        default_factory=list,
        description="A list of required agent capabilities (e.g., 'code_generation', 'context_window_200k')."
    )

    # --- Cost & Quality Control ---
    max_cost_usd: Optional[float] = Field(
        default=None,
        description="The maximum budget for this request in USD."
    )
    quality_tier: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="The desired quality tier, used by the router to select an appropriate model."
    )

    # --- Standard Model Parameters ---
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness. Lower is more deterministic."
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="The maximum number of tokens to generate in the response."
    )


class AgentResponse(BaseModel):
    """
    Standardized response from the Agent Abstraction Layer.
    Provides a consistent format for results, regardless of the underlying AI provider.
    """

    content: str = Field(
        ...,
        description="The main text content of the agent's response."
    )
    provider_used: str = Field(
        ...,
        description="The name of the provider that handled the request (e.g., 'anthropic')."
    )
    model_name_used: str = Field(
        ...,
        description="The specific model name used for the generation (e.g., 'claude-3-opus-20240229')."
    )

    # --- Observability & Metadata ---
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage metadata, typically containing 'input_tokens' and 'output_tokens'."
    )
    cost_usd: float = Field(
        ...,
        description="The calculated cost of the request in USD."
    )
    latency_ms: int = Field(
        ...,
        description="The total time taken for the request to be processed, in milliseconds."
    )

    error: Optional[str] = Field(
        default=None,
        description="If an error occurred, this field contains the error message."
    )
