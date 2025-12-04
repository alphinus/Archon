"""
Chaos Engine for Archon

Implements chaos engineering to validate system resilience.
Simulates failures, network issues, and resource constraints.
"""

import asyncio
import random
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChaosType(Enum):
    """Types of chaos scenarios."""
    REDIS_FAILURE = "redis_failure"
    POSTGRES_FAILURE = "postgres_failure"
    NETWORK_LATENCY = "network_latency"
    CPU_PRESSURE = "cpu_pressure"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_PRESSURE = "disk_pressure"
    SERVICE_CRASH = "service_crash"
    PACKET_LOSS = "packet_loss"


class ChaosEngine:
    """
    Chaos engineering engine for testing system resilience.
    
    Simulates various failure scenarios to validate:
    - Self-healing capabilities
    - Graceful degradation
    - Error recovery
    - Circuit breakers
    - Retry logic
    
    Example:
        engine = ChaosEngine()
        result = await engine.run_chaos_test(
            scenario=ChaosType.REDIS_FAILURE,
            duration=30,
            validate_recovery=True
        )
    """
    
    def __init__(self):
        """Initialize chaos engine."""
        self.active_chaos = []
        self.results = []
    
    async def run_chaos_test(
        self,
        scenario: ChaosType,
        duration: int = 30,
        intensity: float = 0.5,
        validate_recovery: bool = True
    ) -> Dict[str, Any]:
        """
        Run chaos test scenario.
        
        Args:
            scenario: Type of chaos to inject
            duration: Duration in seconds
            intensity: Chaos intensity (0.0 to 1.0)
            validate_recovery: Check if system recovers
        
        Returns:
            Test results with recovery metrics
        
        Example:
            result = await engine.run_chaos_test(
                scenario=ChaosType.REDIS_FAILURE,
                duration=30,
                intensity=0.8
            )
        """
        logger.info(
            f"Running chaos test: {scenario.value} "
            f"(duration={duration}s, intensity={intensity})"
        )
        
        start_time = datetime.now()
        
        # Record baseline health
        baseline_health = await self._check_system_health()
        
        # Inject chaos
        chaos_id = await self._inject_chaos(scenario, intensity)
        self.active_chaos.append(chaos_id)
        
        # Monitor system during chaos
        chaos_metrics = []
        
        for i in range(duration):
            await asyncio.sleep(1)
            
            health = await self._check_system_health()
            chaos_metrics.append({
                "timestamp": datetime.now().isoformat(),
                "health": health,
                "elapsed": i + 1
            })
            
            logger.debug(f"Chaos test {scenario.value}: {i+1}s - Health: {health}")
        
        # Stop chaos
        await self._stop_chaos(chaos_id)
        self.active_chaos.remove(chaos_id)
        
        # Wait for recovery if requested
        recovery_time = None
        if validate_recovery:
            recovery_time = await self._wait_for_recovery(
                baseline_health,
                timeout=60
            )
        
        end_time = datetime.now()
        
        # Calculate results
        result = {
            "scenario": scenario.value,
            "status": "success",
            "duration": duration,
            "intensity": intensity,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "baseline_health": baseline_health,
            "chaos_metrics": chaos_metrics,
            "recovery_time_seconds": recovery_time,
            "recovered": recovery_time is not None if validate_recovery else None,
            "insights": self._analyze_chaos_metrics(chaos_metrics, baseline_health)
        }
        
        self.results.append(result)
        
        logger.info(
            f"Chaos test complete: {scenario.value} - "
            f"Recovery time: {recovery_time}s"
        )
        
        return result
    
    async def run_chaos_monkey(
        self,
        duration: int = 300,
        scenarios: Optional[List[ChaosType]] = None,
        random_intensity: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run random chaos scenarios (Chaos Monkey).
        
        Args:
            duration: Total duration in seconds
            scenarios: List of scenarios to choose from (None for all)
            random_intensity: Randomize intensity
        
        Returns:
            List of test results
        """
        logger.info(f"Starting Chaos Monkey: {duration}s")
        
        scenarios = scenarios or list(ChaosType)
        results = []
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration:
            # Pick random scenario
            scenario = random.choice(scenarios)
            
            # Random test duration (5-30s)
            test_duration = random.randint(5, 30)
            
            # Random intensity
            intensity = random.uniform(0.3, 0.9) if random_intensity else 0.5
            
            # Run chaos test
            result = await self.run_chaos_test(
                scenario=scenario,
                duration=test_duration,
                intensity=intensity
            )
            
            results.append(result)
            
            # Wait between tests (5-15s)
            await asyncio.sleep(random.randint(5, 15))
        
        logger.info(f"Chaos Monkey complete: {len(results)} scenarios executed")
        
        return results
    
    async def _inject_chaos(self, scenario: ChaosType, intensity: float) -> str:
        """
        Inject chaos into system.
        
        Returns chaos ID for cleanup.
        """
        chaos_id = f"{scenario.value}_{datetime.now().timestamp()}"
        
        injectors = {
            ChaosType.REDIS_FAILURE: self._inject_redis_failure,
            ChaosType.POSTGRES_FAILURE: self._inject_postgres_failure,
            ChaosType.NETWORK_LATENCY: self._inject_network_latency,
            ChaosType.CPU_PRESSURE: self._inject_cpu_pressure,
            ChaosType.MEMORY_PRESSURE: self._inject_memory_pressure,
            ChaosType.SERVICE_CRASH: self._inject_service_crash,
        }
        
        if scenario in injectors:
            await injectors[scenario](chaos_id, intensity)
        
        logger.info(f"Chaos injected: {chaos_id}")
        
        return chaos_id
    
    async def _stop_chaos(self, chaos_id: str):
        """Stop chaos injection."""
        logger.info(f"Stopping chaos: {chaos_id}")
        
        # Implementation would stop specific chaos
        # For now, just log
        pass
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        # This would integrate with actual health checks
        # For now, return mock data
        
        return {
            "redis": random.choice(["healthy", "degraded"]),
            "postgres": random.choice(["healthy", "degraded"]),
            "server": random.choice(["healthy", "degraded"]),
            "agents": random.choice(["healthy", "degraded"]),
            "overall_score": random.uniform(0.5, 1.0)
        }
    
    async def _wait_for_recovery(
        self,
        baseline_health: Dict[str, Any],
        timeout: int = 60
    ) -> Optional[float]:
        """
        Wait for system to recover to baseline health.
        
        Returns recovery time in seconds, or None if timeout.
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            current_health = await self._check_system_health()
            
            # Check if recovered (simplified logic)
            if current_health.get("overall_score", 0) >= baseline_health.get("overall_score", 1.0) * 0.9:
                recovery_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"System recovered in {recovery_time:.2f}s")
                return recovery_time
            
            await asyncio.sleep(1)
        
        logger.warning(f"System did not recover within {timeout}s")
        return None
    
    def _analyze_chaos_metrics(
        self,
        metrics: List[Dict[str, Any]],
        baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze chaos test metrics."""
        if not metrics:
            return {}
        
        # Calculate average health score during chaos
        health_scores = [m["health"].get("overall_score", 0) for m in metrics]
        avg_health = sum(health_scores) / len(health_scores)
        
        # Check if system degraded gracefully
        min_health = min(health_scores)
        graceful_degradation = min_health > 0.3  # System stayed above 30% health
        
        return {
            "average_health_during_chaos": avg_health,
            "minimum_health": min_health,
            "graceful_degradation": graceful_degradation,
            "health_variance": max(health_scores) - min(health_scores)
        }
    
    # Chaos injection methods (simplified implementations)
    
    async def _inject_redis_failure(self, chaos_id: str, intensity: float):
        """Simulate Redis failure."""
        logger.info(f"{chaos_id}: Injecting Redis failure (intensity={intensity})")
        # In production: docker compose stop redis or network partition
    
    async def _inject_postgres_failure(self, chaos_id: str, intensity: float):
        """Simulate Postgres failure."""
        logger.info(f"{chaos_id}: Injecting Postgres failure (intensity={intensity})")
        # In production: docker compose stop postgres
    
    async def _inject_network_latency(self, chaos_id: str, intensity: float):
        """Simulate network latency."""
        latency_ms = int(intensity * 1000)  # Up to 1 second
        logger.info(f"{chaos_id}: Injecting network latency ({latency_ms}ms)")
        # In production: tc qdisc add dev eth0 root netem delay {latency_ms}ms
    
    async def _inject_cpu_pressure(self, chaos_id: str, intensity: float):
        """Simulate CPU pressure."""
        cpu_percent = int(intensity * 100)
        logger.info(f"{chaos_id}: Injecting CPU pressure ({cpu_percent}%)")
        # In production: stress --cpu 4 --timeout 30s
    
    async def _inject_memory_pressure(self, chaos_id: str, intensity: float):
        """Simulate memory pressure."""
        memory_mb = int(intensity * 1024)
        logger.info(f"{chaos_id}: Injecting memory pressure ({memory_mb}MB)")
        # In production: stress --vm 1 --vm-bytes {memory_mb}M
    
    async def _inject_service_crash(self, chaos_id: str, intensity: float):
        """Simulate service crash."""
        logger.info(f"{chaos_id}: Injecting service crash")
        # In production: docker compose restart archon-server
