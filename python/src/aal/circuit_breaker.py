# AI Empire HQ - Circuit Breaker Pattern for AAL
# Version: 1.0

import time
from enum import Enum
from typing import Dict, Optional

from structlog import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation for provider fault tolerance.

    Prevents repeated calls to a failing provider, allowing time for recovery.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Provider is failing, requests are rejected immediately
    - HALF_OPEN: Testing if provider has recovered

    Transitions:
    - CLOSED → OPEN: After failure_threshold consecutive failures
    - OPEN → HALF_OPEN: After timeout_seconds has elapsed
    - HALF_OPEN → CLOSED: After a successful request
    - HALF_OPEN → OPEN: If request fails during testing
    """

    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker for a provider.

        Args:
            provider_name: Name of the provider this circuit breaker monitors.
            failure_threshold: Number of consecutive failures before opening circuit.
            timeout_seconds: How long to wait before attempting recovery.
            success_threshold: Number of successes needed to close circuit from half-open.
        """
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._logger = logger.bind(provider=provider_name, component="circuit_breaker")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, potentially transitioning from OPEN to HALF_OPEN"""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self._last_failure_time is None:
            return False
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.timeout_seconds

    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN state"""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._logger.info(
            "circuit_state_transition",
            from_state="open",
            to_state="half_open",
            message="Attempting to test provider recovery"
        )

    def is_request_allowed(self) -> bool:
        """
        Check if a request should be allowed through the circuit breaker.

        Returns:
            True if request is allowed, False if circuit is open.
        """
        current_state = self.state  # This may trigger OPEN → HALF_OPEN transition

        if current_state == CircuitState.OPEN:
            self._logger.debug("circuit_request_blocked", state="open")
            return False

        return True

    def record_success(self):
        """Record a successful request"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._logger.debug(
                "circuit_success_recorded",
                state="half_open",
                success_count=self._success_count,
                threshold=self.success_threshold
            )

            if self._success_count >= self.success_threshold:
                self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            if self._failure_count > 0:
                self._logger.debug("circuit_failure_count_reset", previous_count=self._failure_count)
                self._failure_count = 0

    def _transition_to_closed(self):
        """Transition to CLOSED state (normal operation)"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._logger.info(
            "circuit_state_transition",
            from_state="half_open",
            to_state="closed",
            message="Provider recovered, circuit closed"
        )

    def record_failure(self):
        """Record a failed request"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._logger.warning(
                "circuit_failure_during_recovery",
                state="half_open",
                message="Provider still failing, reopening circuit"
            )
            self._transition_to_open()
        elif self._state == CircuitState.CLOSED:
            self._logger.debug(
                "circuit_failure_recorded",
                failure_count=self._failure_count,
                threshold=self.failure_threshold
            )

            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state (rejecting requests)"""
        self._state = CircuitState.OPEN
        self._success_count = 0
        self._logger.warning(
            "circuit_state_transition",
            from_state=self._state.value if self._state != CircuitState.OPEN else "closed",
            to_state="open",
            failure_count=self._failure_count,
            timeout_seconds=self.timeout_seconds,
            message=f"Circuit opened due to {self._failure_count} failures"
        )

    def get_stats(self) -> Dict[str, any]:
        """
        Get current circuit breaker statistics.

        Returns:
            Dictionary with current state and counters.
        """
        return {
            "provider": self.provider_name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "failure_threshold": self.failure_threshold,
            "timeout_seconds": self.timeout_seconds,
        }


class CircuitBreakerRegistry:
    """
    Registry to manage circuit breakers for all providers.

    Singleton pattern to ensure consistent circuit breaker state across the application.
    """

    _instance: Optional['CircuitBreakerRegistry'] = None

    def __new__(cls) -> 'CircuitBreakerRegistry':
        if cls._instance is None:
            cls._instance = super(CircuitBreakerRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker registry.

        Args:
            failure_threshold: Default failure threshold for new circuit breakers.
            timeout_seconds: Default timeout for new circuit breakers.
            success_threshold: Default success threshold for new circuit breakers.
        """
        if self._initialized:
            return

        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._timeout_seconds = timeout_seconds
        self._success_threshold = success_threshold
        self._logger = logger.bind(component="circuit_breaker_registry")
        self._initialized = True

    def get_circuit_breaker(self, provider_name: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a provider.

        Args:
            provider_name: Name of the provider.

        Returns:
            CircuitBreaker instance for the provider.
        """
        if provider_name not in self._circuit_breakers:
            self._circuit_breakers[provider_name] = CircuitBreaker(
                provider_name=provider_name,
                failure_threshold=self._failure_threshold,
                timeout_seconds=self._timeout_seconds,
                success_threshold=self._success_threshold
            )
            self._logger.info("circuit_breaker_created", provider=provider_name)

        return self._circuit_breakers[provider_name]

    def get_all_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Get statistics for all circuit breakers.

        Returns:
            Dictionary mapping provider names to their circuit breaker stats.
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self._circuit_breakers.items()
        }


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """
    Get the singleton circuit breaker registry instance.

    Returns:
        CircuitBreakerRegistry instance.
    """
    return CircuitBreakerRegistry()
