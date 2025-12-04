"""
Performance Monitor for Archon

Benchmarks system performance and tracks metrics over time.
Provides latency tracking, throughput measurement, and regression detection.
"""

import asyncio
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring and benchmarking for Archon.
    
    Features:
    - Latency tracking (p50, p95, p99)
    - Throughput measurement
    - Memory profiling
    - Performance regression detection
    - Load testing
    
    Example:
        monitor = PerformanceMonitor()
        result = await monitor.benchmark(
            component="memory_write",
            operation=write_func,
            iterations=1000
        )
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.benchmarks = defaultdict(list)
        self.baselines = {}
    
    async def benchmark(
        self,
        component: str,
        operation: Callable,
        iterations: int = 100,
        warmup: int = 10,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Benchmark an operation.
        
        Args:
            component: Component name
            operation: Async callable to benchmark
            iterations: Number of iterations
            warmup: Warmup iterations
            *args, **kwargs: Arguments for operation
        
        Returns:
            Benchmark results with percentiles
        
        Example:
            result = await monitor.benchmark(
                component="memory_read",
                operation=read_memory,
                iterations=1000,
                key="test_key"
            )
        """
        logger.info(f"Benchmarking {component}: {iterations} iterations")
        
        # Warmup
        for _ in range(warmup):
            await operation(*args, **kwargs)
        
        # Benchmark
        latencies = []
        errors = 0
        
        for i in range(iterations):
            start = time.perf_counter()
            
            try:
                await operation(*args, **kwargs)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
            except Exception as e:
                logger.error(f"Benchmark iteration {i} failed: {e}")
                errors += 1
        
        # Calculate statistics
        if latencies:
            result = {
                "component": component,
                "iterations": iterations,
                "errors": errors,
                "success_rate": (iterations - errors) / iterations,
                "latency_ms": {
                    "min": min(latencies),
                    "max": max(latencies),
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "p50": self._percentile(latencies, 50),
                    "p95": self._percentile(latencies, 95),
                    "p99": self._percentile(latencies, 99),
                    "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            result = {
                "component": component,
                "iterations": iterations,
                "errors": errors,
                "success_rate": 0,
                "error": "All iterations failed"
            }
        
        # Store benchmark
        self.benchmarks[component].append(result)
        
        logger.info(
            f"Benchmark complete: {component} - "
            f"p50={result.get('latency_ms', {}).get('p50', 0):.2f}ms, "
            f"p95={result.get('latency_ms', {}).get('p95', 0):.2f}ms"
        )
        
        return result
    
    async def load_test(
        self,
        component: str,
        operation: Callable,
        target_rps: int = 100,
        duration: int = 60,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run load test at target requests per second.
        
        Args:
            component: Component name
            operation: Operation to test
            target_rps: Target requests per second
            duration: Test duration in seconds
            *args, **kwargs: Operation arguments
        
        Returns:
            Load test results
        
        Example:
            result = await monitor.load_test(
                component="api_endpoint",
                operation=call_api,
                target_rps=100,
                duration=60
            )
        """
        logger.info(
            f"Load testing {component}: {target_rps} RPS for {duration}s"
        )
        
        delay_between_requests = 1.0 / target_rps
        
        start_time = time.time()
        end_time = start_time + duration
        
        latencies = []
        errors = 0
        total_requests = 0
        
        while time.time() < end_time:
            request_start = time.perf_counter()
            
            try:
                await operation(*args, **kwargs)
                request_end = time.perf_counter()
                latencies.append((request_end - request_start) * 1000)
            except Exception as e:
                logger.debug(f"Load test request failed: {e}")
                errors += 1
            
            total_requests += 1
            
            # Wait to maintain target RPS
            await asyncio.sleep(delay_between_requests)
        
        actual_duration = time.time() - start_time
        actual_rps = total_requests / actual_duration
        
        result = {
            "component": component,
            "target_rps": target_rps,
            "actual_rps": actual_rps,
            "duration": actual_duration,
            "total_requests": total_requests,
            "errors": errors,
            "success_rate": (total_requests - errors) / total_requests,
            "latency_ms": {
                "p50": self._percentile(latencies, 50),
                "p95": self._percentile(latencies, 95),
                "p99": self._percentile(latencies, 99),
                "mean": statistics.mean(latencies)
            } if latencies else {},
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"Load test complete: {component} - "
            f"Actual RPS: {actual_rps:.2f}, "
            f"p95: {result['latency_ms'].get('p95', 0):.2f}ms"
        )
        
        return result
    
    def set_baseline(self, component: str, benchmark_result: Dict[str, Any]):
        """
        Set performance baseline for regression detection.
        
        Args:
            component: Component name
            benchmark_result: Baseline benchmark result
        """
        self.baselines[component] = benchmark_result
        logger.info(f"Baseline set for {component}")
    
    def detect_regression(
        self,
        component: str,
        current_result: Dict[str, Any],
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Detect performance regression against baseline.
        
        Args:
            component: Component name
            current_result: Current benchmark result
            threshold: Regression threshold (0.2 = 20% slower)
        
        Returns:
            Regression analysis
        
        Example:
            analysis = monitor.detect_regression(
                component="memory_write",
                current_result=latest_benchmark,
                threshold=0.2  # 20% slower = regression
            )
        """
        if component not in self.baselines:
            return {
                "has_regression": False,
                "reason": "No baseline set"
            }
        
        baseline = self.baselines[component]
        current = current_result
        
        # Compare p95 latency
        baseline_p95 = baseline.get("latency_ms", {}).get("p95", 0)
        current_p95 = current.get("latency_ms", {}).get("p95", 0)
        
        if baseline_p95 == 0:
            return {
                "has_regression": False,
                "reason": "Invalid baseline"
            }
        
        change = (current_p95 - baseline_p95) / baseline_p95
        
        has_regression = change > threshold
        
        return {
            "has_regression": has_regression,
            "baseline_p95_ms": baseline_p95,
            "current_p95_ms": current_p95,
            "change_percent": change * 100,
            "threshold_percent": threshold * 100,
            "severity": "critical" if change > threshold * 2 else "warning" if has_regression else "ok"
        }
    
    def get_performance_report(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance report.
        
        Args:
            component: Specific component (None for all)
        
        Returns:
            Performance report
        """
        if component:
            benchmarks = self.benchmarks.get(component, [])
            return {
                "component": component,
                "benchmark_count": len(benchmarks),
                "latest": benchmarks[-1] if benchmarks else None,
                "baseline": self.baselines.get(component)
            }
        else:
            return {
                comp: {
                    "benchmark_count": len(benchmarks),
                    "latest": benchmarks[-1] if benchmarks else None,
                    "baseline": self.baselines.get(comp)
                }
                for comp, benchmarks in self.benchmarks.items()
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
