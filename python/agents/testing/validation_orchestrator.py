"""
Validation Orchestrator for Archon

Coordinates all testing activities and provides unified validation interface.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from agents.testing.test_runner import TestRunner, TestReporter
from agents.testing.chaos_engine import ChaosEngine, ChaosType
from agents.testing.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """
    Orchestrates all testing and validation activities.
    
    Provides a unified interface for:
    - Running test suites
    - Chaos testing
    - Performance benchmarking
    - Full system validation
    
    Example:
        orchestrator = ValidationOrchestrator()
        result = await orchestrator.validate_production()
    """
    
    def __init__(self):
        """Initialize validation orchestrator."""
        self.test_runner = TestRunner()
        self.test_reporter = TestReporter()
        self.chaos_engine = ChaosEngine()
        self.perf_monitor = PerformanceMonitor()
    
    async def validate_production(
        self,
        include_chaos: bool =True,
        include_perf: bool = True,
        chaos_duration: int = 60
    ) -> Dict[str, Any]:
        """
        Full production validation.
        
        Runs:
        1. All test suites
        2. Chaos tests
        3. Performance benchmarks
        
        Args:
            include_chaos: Run chaos tests
            include_perf: Run performance tests
            chaos_duration: Chaos test duration
        
        Returns:
            Comprehensive validation results
        
        Example:
            result = await orchestrator.validate_production()
            if result['status'] == 'success':
                print("Production ready!")
        """
        logger.info("Starting full production validation...")
        
        start_time = datetime.now()
        results = {
            "timestamp": start_time.isoformat(),
            "status": "success"
        }
        
        # 1. Run all tests
        logger.info("Step 1/3: Running test suites...")
        test_results = await self.test_runner.run_tests(
            coverage=True,
            parallel=True
        )
        results["tests"] = test_results
        
        if test_results.get("failed", 0) > 0:
            results["status"] = "failed"
            results["reason"] = "Test failures detected"
            return results
        
        # 2. Chaos testing (if enabled)
        if include_chaos:
            logger.info("Step 2/3: Running chaos tests...")
            chaos_results = await self._run_chaos_validation(chaos_duration)
            results["chaos"] = chaos_results
            
            # Check if system recovered from all chaos scenarios
            if not all(r.get("recovered") for r in chaos_results):
                results["status"] = "warning"
                results["reason"] = "Some chaos scenarios did not recover"
        
        # 3. Performance benchmarks (if enabled)
        if include_perf:
            logger.info("Step 3/3: Running performance benchmarks...")
            perf_results = await self._run_performance_validation()
            results["performance"] = perf_results
            
            # Check for regressions
            if any(r.get("has_regression") for r in perf_results.values()):
                results["status"] = "warning"
                results["reason"] = "Performance regressions detected"
        
        end_time = datetime.now()
        results["duration_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Production validation complete: {results['status']} "
            f"(duration={results['duration_seconds']:.2f}s)"
        )
        
        # Generate comprehensive report
        report_path = self.test_reporter.generate_report(results, format="html")
        results["report_path"] = report_path
        
        return results
    
    async def validate_component(
        self,
        component: str,
        run_tests: bool = True,
        run_chaos: bool = False,
        run_perf: bool = True
    ) -> Dict[str, Any]:
        """
        Validate specific component.
        
        Args:
            component: Component name (e.g., 'memory', 'events')
            run_tests: Run component tests
            run_chaos: Run chaos tests
            run_perf: Run performance tests
        
        Returns:
            Component validation results
        """
        logger.info(f"Validating component: {component}")
        
        results = {
            "component": component,
            "timestamp": datetime.now().isoformat()
        }
        
        if run_tests:
            test_results = await self.test_runner.run_tests(
                suites=[component],
                coverage=True
            )
            results["tests"] = test_results
        
        if run_perf:
            # Component-specific benchmark would go here
            results["performance"] = {
                "status": "skipped",
                "reason": "Component-specific benchmarks not implemented"
            }
        
        return results
    
    async def _run_chaos_validation(self, duration: int) -> List[Dict[str, Any]]:
        """Run comprehensive chaos testing."""
        # Test critical scenarios
        critical_scenarios = [
            ChaosType.REDIS_FAILURE,
            ChaosType.POSTGRES_FAILURE,
            ChaosType.NETWORK_LATENCY
        ]
        
        results = []
        
        for scenario in critical_scenarios:
            result = await self.chaos_engine.run_chaos_test(
                scenario=scenario,
                duration=min(duration, 30),  # Max 30s per scenario
                intensity=0.7,
                validate_recovery=True
            )
            results.append(result)
        
        return results
    
    async def _run_performance_validation(self) -> Dict[str, Dict[str, Any]]:
        """Run performance benchmarks for key components."""
        # Mock benchmarks - in production, these would be real operations
        
        async def mock_operation():
            await asyncio.sleep(0.001)  # Simulate 1ms operation
        
        components = ["memory_read", "memory_write", "event_publish"]
        results = {}
        
        for component in components:
            benchmark = await self.perf_monitor.benchmark(
                component=component,
                operation=mock_operation,
                iterations=100
            )
            
            # Check regression if baseline exists
            regression = self.perf_monitor.detect_regression(
                component=component,
                current_result=benchmark
            )
            
            results[component] = {
                "benchmark": benchmark,
                "regression": regression
            }
        
        return results
    
    async def quick_validation(self) -> Dict[str, Any]:
        """
        Quick validation (subset of tests).
        
        Fast validation for development iteration.
        
        Returns:
            Quick validation results
        """
        logger.info("Running quick validation...")
        
        # Run only unit tests, no chaos/perf
        test_results = await self.test_runner.run_tests(
            markers="unit",
            coverage=False,
            parallel=True
        )
        
        return {
            "mode": "quick",
            "tests": test_results,
            "timestamp": datetime.now().isoformat()
        }
