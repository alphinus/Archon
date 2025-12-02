"""
Prometheus metrics collection for Archon.
Exposes metrics at /metrics endpoint for scraping.
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from structlog import get_logger

logger = get_logger(__name__)

# Request metrics
http_requests_total = Counter(
    'archon_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'archon_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_errors_total = Counter(
    'archon_http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# Memory system metrics
memory_sessions_active = Gauge(
    'archon_memory_sessions_active',
    'Number of active memory sessions'
)

memory_entries_total = Gauge(
    'archon_memory_entries_total',
    'Total memory entries',
    ['memory_type']  # session, working, longterm
)

memory_operations_total = Counter(
    'archon_memory_operations_total',
    'Total memory operations',
    ['operation', 'memory_type']  # create, read, update, delete
)

# External service metrics
external_service_requests_total = Counter(
    'archon_external_service_requests_total',
    'Total external service requests',
    ['service', 'operation', 'status']
)

external_service_duration_seconds = Histogram(
    'archon_external_service_duration_seconds',
    'External service request duration',
    ['service', 'operation']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'archon_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)

circuit_breaker_failures_total = Counter(
    'archon_circuit_breaker_failures_total',
    'Circuit breaker failures',
    ['service']
)

# Database metrics
database_query_duration_seconds = Histogram(
    'archon_database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

database_connections_active = Gauge(
    'archon_database_connections_active',
    'Active database connections'
)

# Cache metrics
cache_hits_total = Counter(
    'archon_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'archon_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


def track_request(method: str, endpoint: str, status: int):
    """Track an HTTP request."""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()


def track_error(method: str, endpoint: str, error_type: str):
    """Track an HTTP error."""
    http_errors_total.labels(
        method=method,
        endpoint=endpoint,
        error_type=error_type
    ).inc()


def track_memory_operation(operation: str, memory_type: str):
    """Track a memory operation."""
    memory_operations_total.labels(
        operation=operation,
        memory_type=memory_type
    ).inc()


def set_active_sessions(count: int):
    """Set the number of active sessions."""
    memory_sessions_active.set(count)


def set_memory_entries(memory_type: str, count: int):
    """Set the number of memory entries."""
    memory_entries_total.labels(memory_type=memory_type).set(count)


def track_external_service(service: str, operation: str, status: str, duration: float):
    """Track an external service request."""
    external_service_requests_total.labels(
        service=service,
        operation=operation,
        status=status
    ).inc()
    
    external_service_duration_seconds.labels(
        service=service,
        operation=operation
    ).observe(duration)


def set_circuit_breaker_state(service: str, state: int):
    """
    Set circuit breaker state.
    0 = CLOSED, 1 = OPEN, 2 = HALF_OPEN
    """
    circuit_breaker_state.labels(service=service).set(state)


def track_circuit_breaker_failure(service: str):
    """Track a circuit breaker failure."""
    circuit_breaker_failures_total.labels(service=service).inc()


def track_cache_hit(cache_type: str):
    """Track a cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Track a cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()
