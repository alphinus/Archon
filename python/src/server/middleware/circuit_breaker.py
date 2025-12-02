"""
Circuit breaker implementation for external service resilience.
Prevents cascading failures by failing fast when a service is down.
"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from structlog import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Opens circuit after failure_threshold failures within window_seconds.
    Stays open for timeout_seconds before attempting recovery.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        window_seconds: int = 60
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.window_seconds = window_seconds
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if circuit is closed
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"circuit_breaker_half_open", name=self.name)
            else:
                from src.server.exceptions import CircuitBreakerOpenError
                raise CircuitBreakerOpenError(service=self.name)
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call()."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"circuit_breaker_half_open", name=self.name)
            else:
                from src.server.exceptions import CircuitBreakerOpenError
                raise CircuitBreakerOpenError(service=self.name)
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"circuit_breaker_recovered", name=self.name)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.opened_at = None
    
    def _on_failure(self):
        """Record failed call."""
        current_time = time.time()
        
        # Reset counter if outside window
        if (self.last_failure_time and 
            current_time - self.last_failure_time > self.window_seconds):
            self.failure_count = 0
        
        self.failure_count += 1
        self.last_failure_time = current_time
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = current_time
            logger.error(
                f"circuit_breaker_opened",
                name=self.name,
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.opened_at:
            return False
        return time.time() - self.opened_at >= self.timeout_seconds


# Global circuit breakers for external services
_circuit_breakers = {}


def get_circuit_breaker(service_name: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(name=service_name, **kwargs)
    return _circuit_breakers[service_name]
