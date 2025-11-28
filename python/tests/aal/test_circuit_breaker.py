"""Tests for Circuit Breaker implementation"""

import pytest
import time
from aal.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerRegistry


class TestCircuitBreaker:
    """Test Circuit Breaker functionality"""

    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state"""
        cb = CircuitBreaker("test-provider")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_request_allowed()

    def test_opens_after_threshold_failures(self):
        """Circuit breaker should open after failure threshold is reached"""
        cb = CircuitBreaker("test-provider", failure_threshold=3)

        # Record failures below threshold
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        # Exceed threshold - should open
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert not cb.is_request_allowed()

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit breaker should transition to HALF_OPEN after timeout"""
        cb = CircuitBreaker("test-provider", failure_threshold=2, timeout_seconds=1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Check state - should transition to HALF_OPEN
        state = cb.state  # Accessing state triggers transition check
        assert state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        """Circuit breaker should close after successes in HALF_OPEN state"""
        cb = CircuitBreaker("test-provider", failure_threshold=2, timeout_seconds=1, success_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for timeout and transition to HALF_OPEN
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Circuit breaker should reopen if failure occurs in HALF_OPEN"""
        cb = CircuitBreaker("test-provider", failure_threshold=2, timeout_seconds=1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN

        # Record failure - should reopen
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_resets_failure_count_on_success(self):
        """Failure count should reset on success in CLOSED state"""
        cb = CircuitBreaker("test-provider", failure_threshold=3)

        cb.record_failure()
        cb.record_success()  # Should reset failure count
        cb.record_failure()

        # Should still be closed (only 1 failure after reset)
        assert cb.state == CircuitState.CLOSED

    def test_get_stats_returns_correct_data(self):
        """get_stats should return current breaker statistics"""
        cb = CircuitBreaker("test-provider", failure_threshold=5, timeout_seconds=60)

        stats = cb.get_stats()

        assert stats["provider"] == "test-provider"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["failure_threshold"] == 5
        assert stats["timeout_seconds"] == 60


class TestCircuitBreakerRegistry:
    """Test Circuit Breaker Registry"""

    def test_get_circuit_breaker_creates_new(self):
        """Registry should create new circuit breaker if not exists"""
        registry = CircuitBreakerRegistry()
        cb = registry.get_circuit_breaker("new-provider")

        assert cb is not None
        assert cb.provider_name == "new-provider"

    def test_get_circuit_breaker_returns_same_instance(self):
        """Registry should return same circuit breaker instance"""
        registry = CircuitBreakerRegistry()

        cb1 = registry.get_circuit_breaker("provider-1")
        cb2 = registry.get_circuit_breaker("provider-1")

        assert cb1 is cb2

    def test_get_all_stats_returns_all_breakers(self):
        """get_all_stats should return stats for all registered breakers"""
        registry = CircuitBreakerRegistry()

        registry.get_circuit_breaker("provider-1")
        registry.get_circuit_breaker("provider-2")

        all_stats = registry.get_all_stats()

        assert len(all_stats) >= 2  # May have more from other tests
        assert "provider-1" in all_stats or "provider-2" in all_stats

    def test_singleton_pattern(self):
        """Registry should be a singleton"""
        registry1 = CircuitBreakerRegistry()
        registry2 = CircuitBreakerRegistry()

        assert registry1 is registry2
