# AI Empire HQ - AAL Prometheus Metrics
# Version: 1.0

"""
Prometheus metrics for the Agent Abstraction Layer.

Tracks:
- Request counts by provider and status
- Request latency by provider
- Request costs by provider and model
- Token usage by provider
- Circuit breaker states
"""

from prometheus_client import Counter, Histogram, Gauge, Info


# Request Metrics
aal_requests_total = Counter(
    'aal_requests_total',
    'Total number of AAL requests',
    ['provider', 'status', 'quality_tier']
)

aal_requests_latency_seconds = Histogram(
    'aal_requests_latency_seconds',
    'AAL request latency in seconds',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# Cost Metrics
aal_requests_cost_usd = Histogram(
    'aal_requests_cost_usd',
    'AAL request cost in USD',
    ['provider', 'model'],
    buckets=(0.0001, 0.001, 0.01, 0.1, 1.0, 10.0)
)

aal_cumulative_cost_usd = Counter(
    'aal_cumulative_cost_usd',
    'Cumulative AAL costs in USD',
    ['provider', 'model']
)

# Token Metrics
aal_tokens_total = Counter(
    'aal_tokens_total',
    'Total tokens processed by AAL',
    ['provider', 'model', 'token_type']  # token_type: input or output
)

# Circuit Breaker Metrics
aal_circuit_breaker_state = Gauge(
    'aal_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['provider']
)

aal_circuit_breaker_failures = Counter(
    'aal_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['provider']
)

aal_circuit_breaker_transitions = Counter(
    'aal_circuit_breaker_transitions_total',
    'Total circuit breaker state transitions',
    ['provider', 'from_state', 'to_state']
)

# Provider Metrics
aal_provider_info = Info(
    'aal_provider',
    'Information about registered AAL providers'
)

aal_provider_available = Gauge(
    'aal_provider_available',
    'Provider availability (1=available, 0=unavailable)',
    ['provider']
)

# Routing Metrics
aal_routing_capability_filters = Counter(
    'aal_routing_capability_filters_total',
    'Requests filtered by capability requirements',
    ['required_capability']
)

aal_routing_cost_filters = Counter(
    'aal_routing_cost_filters_total',
    'Requests filtered by cost constraints',
    ['provider']
)

aal_routing_fallbacks = Counter(
    'aal_routing_fallbacks_total',
    'Provider fallback attempts',
    ['from_provider', 'to_provider']
)

# Agent Performance Metrics
aal_agent_requests = Counter(
    'aal_agent_requests_total',
    'Requests by agent/feature',
    ['agent_name', 'provider', 'status']
)

aal_agent_token_efficiency = Histogram(
    'aal_agent_token_efficiency_ratio',
    'Output/Input token ratio by agent',
    ['agent_name'],
    buckets=(0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)
)


class MetricsCollector:
    """
    Helper class to collect and export AAL metrics to Prometheus.
    """

    @staticmethod
    def record_request(provider: str, model: str, quality_tier: str, success: bool):
        """Record a completed request"""
        status = "success" if success else "error"
        aal_requests_total.labels(
            provider=provider,
            status=status,
            quality_tier=quality_tier
        ).inc()

    @staticmethod
    def record_latency(provider: str, model: str, latency_seconds: float):
        """Record request latency"""
        aal_requests_latency_seconds.labels(
            provider=provider,
            model=model
        ).observe(latency_seconds)

    @staticmethod
    def record_cost(provider: str, model: str, cost_usd: float):
        """Record request cost"""
        aal_requests_cost_usd.labels(
            provider=provider,
            model=model
        ).observe(cost_usd)

        aal_cumulative_cost_usd.labels(
            provider=provider,
            model=model
        ).inc(cost_usd)

    @staticmethod
    def record_tokens(provider: str, model: str, input_tokens: int, output_tokens: int):
        """Record token usage"""
        aal_tokens_total.labels(
            provider=provider,
            model=model,
            token_type="input"
        ).inc(input_tokens)

        aal_tokens_total.labels(
            provider=provider,
            model=model,
            token_type="output"
        ).inc(output_tokens)

    @staticmethod
    def record_circuit_breaker_state(provider: str, state: str):
        """
        Record circuit breaker state.

        Args:
            provider: Provider name
            state: Circuit state ("closed", "half_open", "open")
        """
        state_map = {
            "closed": 0,
            "half_open": 1,
            "open": 2
        }
        aal_circuit_breaker_state.labels(provider=provider).set(
            state_map.get(state, -1)
        )

    @staticmethod
    def record_circuit_breaker_failure(provider: str):
        """Record a circuit breaker failure"""
        aal_circuit_breaker_failures.labels(provider=provider).inc()

    @staticmethod
    def record_circuit_breaker_transition(provider: str, from_state: str, to_state: str):
        """Record a circuit breaker state transition"""
        aal_circuit_breaker_transitions.labels(
            provider=provider,
            from_state=from_state,
            to_state=to_state
        ).inc()

    @staticmethod
    def set_provider_info(providers: dict):
        """
        Set provider information.

        Args:
            providers: Dictionary of provider names to their info
        """
        aal_provider_info.info(providers)

    @staticmethod
    def set_provider_available(provider: str, available: bool):
        """Set provider availability"""
        aal_provider_available.labels(provider=provider).set(
            1 if available else 0
        )

    @staticmethod
    def record_capability_filter(capability: str):
        """Record a capability filter application"""
        aal_routing_capability_filters.labels(
            required_capability=capability
        ).inc()

    @staticmethod
    def record_cost_filter(provider: str):
        """Record a cost constraint filter"""
        aal_routing_cost_filters.labels(provider=provider).inc()

    @staticmethod
    def record_fallback(from_provider: str, to_provider: str):
        """Record a provider fallback"""
        aal_routing_fallbacks.labels(
            from_provider=from_provider,
            to_provider=to_provider
        ).inc()

    @staticmethod
    def record_agent_request(agent_name: str, provider: str, success: bool):
        """Record an agent-specific request"""
        status = "success" if success else "error"
        aal_agent_requests.labels(
            agent_name=agent_name,
            provider=provider,
            status=status
        ).inc()

    @staticmethod
    def record_agent_token_efficiency(agent_name: str, input_tokens: int, output_tokens: int):
        """Record token efficiency for an agent"""
        if input_tokens > 0:
            ratio = output_tokens / input_tokens
            aal_agent_token_efficiency.labels(agent_name=agent_name).observe(ratio)
