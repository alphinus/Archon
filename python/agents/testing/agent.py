"""
Testing & Validation Agent

Main agent class that coordinates all testing activities.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from agents.testing.test_runner import TestRunner, TestReporter
from agents.testing.chaos_engine import ChaosEngine, ChaosType
from agents.testing.performance_monitor import PerformanceMonitor
from agents.testing.validation_orchestrator import ValidationOrchestrator
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class TestingAgent(BaseAgent):
    """
    Testing & Validation Agent for Archon.
    
    Provides skills for:
    - Automated test execution
    - Chaos engineering
    - Performance benchmarking
    - Regression detection
    - Production validation
    
    Skills:
    - run_tests: Execute test suites with coverage
    - chaos_test: Run chaos engineering scenarios
    - benchmark: Performance benchmarking
    - validate_production: Full system validation
    - detect_regression: Performance regression detection
    
    Example:
        agent = TestingAgent(
            agent_id="testing",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """
        Initialize Testing Agent.
        
        Args:
            agent_id: Agent identifier (should be 'testing')
            event_bus: Event bus for communication
            memory: Memory system instance
            **config: Additional configuration
        """
        self.config = config
        self.test_runner = TestRunner()
        self.test_reporter = TestReporter()
        self.chaos_engine = ChaosEngine()
        self.perf_monitor = PerformanceMonitor()
        self.orchestrator = ValidationOrchestrator()
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] Testing Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register Testing Agent skills."""
        self.register_skill("run_tests", self.run_tests)
        self.register_skill("chaos_test", self.chaos_test)
        self.register_skill("benchmark", self.benchmark)
        self.register_skill("load_test", self.load_test)
        self.register_skill("validate_production", self.validate_production)
        self.register_skill("detect_regression", self.detect_regression)
    
    async def run_tests(
        self,
        suites: Optional[List[str]] = None,
        coverage: bool = True,
        parallel: bool = True,
        markers: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run test suites.
        
        Args:
            suites: Test suites to run (None for all)
            coverage: Generate coverage report
            parallel: Run in parallel
            markers: Pytest markers
        
        Returns:
            Test results
        
        Example:
            results = await agent.run_tests(
                suites=["memory", "events"],
                coverage=True,
                parallel=True
            )
        """
        logger.info(
            f"[{self.agent_id}] Running tests "
            f"(suites={suites}, coverage={coverage})"
        )
        
        try:
            results = await self.test_runner.run_tests(
                suites=suites,
                coverage=coverage,
                parallel=parallel,
                markers=markers
            )
            
            # Generate report
            if results.get("status") == "success":
                report_path = self.test_reporter.generate_report(results, format="html")
                results["report_path"] = report_path
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Test execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def chaos_test(
        self,
        scenario: str,
        duration: int = 30,
        intensity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Run chaos engineering test.
        
        Args:
            scenario: Chaos scenario (redis_failure, postgres_failure, etc.)
            duration: Duration in seconds
            intensity: Intensity (0.0-1.0)
        
        Returns:
            Chaos test results
        
        Example:
            result = await agent.chaos_test(
                scenario="redis_failure",
                duration=30,
                intensity=0.7
            )
        """
        logger.info(
            f"[{self.agent_id}] Running chaos test: {scenario} "
            f"(duration={duration}s, intensity={intensity})"
        )
        
        try:
            # Convert string to enum
            chaos_type = ChaosType(scenario)
            
            result = await self.chaos_engine.run_chaos_test(
                scenario=chaos_type,
                duration=duration,
                intensity=intensity,
                validate_recovery=True
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except ValueError:
            return {
                "status": "error",
                "error": f"Unknown scenario: {scenario}"
            }
        except Exception as e:
            logger.error(f"[{self.agent_id}] Chaos test failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def benchmark(
        self,
        component: str,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Benchmark component performance.
        
        Args:
            component: Component to benchmark
            iterations: Number of iterations
        
        Returns:
            Benchmark results
        
        Example:
            result = await agent.benchmark(
                component="memory_write",
                iterations=1000
            )
        """
        logger.info(
            f"[{self.agent_id}] Benchmarking {component} "
            f"({iterations} iterations)"
        )
        
        try:
            # Mock operation - in production, this would call actual component
            async def mock_operation():
                import asyncio
                await asyncio.sleep(0.001)
            
            result = await self.perf_monitor.benchmark(
                component=component,
                operation=mock_operation,
                iterations=iterations
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Benchmark failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def load_test(
        self,
        component: str,
        target_rps: int = 100,
        duration: int = 60
    ) -> Dict[str, Any]:
        """
        Run load test.
        
        Args:
            component: Component to test
            target_rps: Target requests per second
            duration: Duration in seconds
        
        Returns:
            Load test results
        
        Example:
            result = await agent.load_test(
                component="api_endpoint",
                target_rps=100,
                duration=60
            )
        """
        logger.info(
            f"[{self.agent_id}] Load testing {component} "
            f"({target_rps} RPS, {duration}s)"
        )
        
        try:
            async def mock_operation():
                import asyncio
                await asyncio.sleep(0.001)
            
            result = await self.perf_monitor.load_test(
                component=component,
                operation=mock_operation,
                target_rps=target_rps,
                duration=duration
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Load test failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def validate_production(
        self,
        include_chaos: bool = True,
        include_perf: bool = True
    ) -> Dict[str, Any]:
        """
        Full production validation.
        
        Args:
            include_chaos: Include chaos tests
            include_perf: Include performance tests
        
        Returns:
            Comprehensive validation results
        
        Example:
            result = await agent.validate_production()
            if result['status'] == 'success':
                print("System is production-ready!")
        """
        logger.info(f"[{self.agent_id}] Running full production validation...")
        
        try:
            result = await self.orchestrator.validate_production(
                include_chaos=include_chaos,
                include_perf=include_perf
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Validation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def detect_regression(
        self,
        component: str,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Detect performance regression.
        
        Args:
            component: Component to check
            threshold: Regression threshold (0.2 = 20%)
        
        Returns:
            Regression analysis
        
        Example:
            result = await agent.detect_regression(
                component="memory_write",
                threshold=0.2
            )
        """
        logger.info(
            f"[{self.agent_id}] Checking regression for {component} "
            f"(threshold={threshold*100}%)"
        )
        
        try:
            # Get latest benchmark
            report = self.perf_monitor.get_performance_report(component)
            latest = report.get("latest")
            
            if not latest:
                return {
                    "status": "error",
                    "error": "No benchmark data available"
                }
            
            regression = self.perf_monitor.detect_regression(
                component=component,
                current_result=latest,
                threshold=threshold
            )
            
            return {
                "status": "success",
                "result": regression
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Regression detection failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


# Entry point for running agent standalone
if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    asyncio.run(run_agent(TestingAgent, "testing"))
