"""
Prometheus Metrics for Archon.
Provides comprehensive observability for production monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

# ============================================================================
# MEMORY SYSTEM METRICS
# ============================================================================

memory_api_requests_total = Counter(
    'archon_memory_api_requests_total',
    'Total number of memory API requests',
    ['operation', 'memory_type', 'status']
)

memory_api_latency_seconds = Histogram(
    'archon_memory_api_latency_seconds',
    'Memory API latency in seconds',
    ['operation', 'memory_type'],
    buckets=(.001, .005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

memory_context_assembly_tokens = Histogram(
    'archon_memory_context_tokens',
    'Tokens in assembled context',
    buckets=(100, 500, 1000, 2000, 4000, 6000, 8000, 10000)
)

memory_cache_hits_total = Counter(
    'archon_memory_cache_hits_total',
    'Memory cache hits',
    ['cache_type']
)

memory_cache_misses_total = Counter(
    'archon_memory_cache_misses_total',
    'Memory cache misses',
    ['cache_type']
)

# ============================================================================
# EVENT SYSTEM METRICS
# ============================================================================

events_published_total = Counter(
    'archon_events_published_total',
    'Total events published',
    ['event_type', 'status']
)

events_processed_total = Counter(
    'archon_events_processed_total',
    'Total events processed',
    ['event_type', 'status']
)

events_dlq_size = Gauge(
    'archon_events_dlq_size',
    'Dead Letter Queue size'
)

events_retry_attempts_total = Counter(
    'archon_events_retry_attempts_total',
    'Event retry attempts',
    ['event_type', 'retry_count']
)

# ============================================================================
# WORKER METRICS
# ============================================================================

worker_runs_total = Counter(
    'archon_worker_runs_total',
    'Worker execution count',
    ['worker_name', 'status']
)

worker_run_duration_seconds = Histogram(
    'archon_worker_run_duration_seconds',
    'Worker execution duration',
    ['worker_name'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

worker_crashes_total = Counter(
    'archon_worker_crashes_total',
    'Worker crashes',
    ['worker_name']
)

worker_health_status = Gauge(
    'archon_worker_health_status',
    'Worker health (1=healthy, 0=unhealthy)',
    ['worker_name']
)

# ============================================================================
# CIRCUIT BREAKER METRICS
# ============================================================================

circuit_breaker_state = Gauge(
    'archon_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

circuit_breaker_failures = Counter(
    'archon_circuit_breaker_failures_total',
    'Circuit breaker triggered failures',
    ['service']
)

# ============================================================================
# SYSTEM HEALTH METRICS
# ============================================================================

system_health_status = Gauge(
    'archon_system_health_status',
    'Overall system health (1=healthy, 0.5=degraded, 0=unhealthy)'
)

component_health_status = Gauge(
    'archon_component_health_status',
    'Component health status (1=healthy, 0.5=degraded, 0=unhealthy)',
    ['component']
)

component_latency_seconds = Gauge(
    'archon_component_latency_seconds',
    'Component latency in seconds',
    ['component']
)

# ============================================================================
# DECORATORS FOR AUTOMATIC INSTRUMENTATION
# ============================================================================

def track_memory_operation(operation: str, memory_type: str):
    """Decorator to automatically track memory operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                memory_api_requests_total.labels(
                    operation=operation,
                    memory_type=memory_type,
                    status=status
                ).inc()
                memory_api_latency_seconds.labels(
                    operation=operation,
                    memory_type=memory_type
                ).observe(duration)
                
        return wrapper
    return decorator

def track_event_operation(event_type: str):
    """Decorator to track event operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                events_published_total.labels(
                    event_type=event_type,
                    status=status
                ).inc()
                
        return wrapper
    return decorator

def track_worker_run(worker_name: str):
    """Decorator to track worker execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                worker_health_status.labels(worker_name=worker_name).set(1)
                return result
            except Exception as e:
                status = "error"
                worker_crashes_total.labels(worker_name=worker_name).inc()
                worker_health_status.labels(worker_name=worker_name).set(0)
                raise
            finally:
                duration = time.time() - start_time
                worker_runs_total.labels(
                    worker_name=worker_name,
                    status=status
                ).inc()
                worker_run_duration_seconds.labels(
                    worker_name=worker_name
                ).observe(duration)
                
        return wrapper
    return decorator

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_circuit_breaker_metrics(service: str, state: str):
    """Update circuit breaker state metrics."""
    state_map = {"closed": 0, "open": 1, "half_open": 2}
    circuit_breaker_state.labels(service=service).set(state_map.get(state, 0))

def update_system_health(status: str):
    """Update overall system health metric."""
    status_map = {"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}
    system_health_status.set(status_map.get(status, 0.0))

def update_component_health(component: str, status: str, latency: float = None):
    """Update component-specific health metrics."""
    status_map = {"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}
    component_health_status.labels(component=component).set(status_map.get(status, 0.0))
    
    if latency is not None:
        component_latency_seconds.labels(component=component).set(latency)
