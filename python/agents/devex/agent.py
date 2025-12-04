"""
Developer Experience (DevEx) Agent

Main agent class that coordinates all developer tools:
- CLI commands
- Hot reload
- Debug tools
- Testing utilities
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from agents.devex.debug_tools import MemoryInspector, EventStreamViewer, PerformanceProfiler
from agents.devex.dev_server import DevServer
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DevExAgent(BaseAgent):
    """
    Developer Experience (DevEx) Agent for Archon.
    
    Provides skills for:
    - Development server management (hot reload)
    - Debugging (memory inspection, event streaming)
    - Performance profiling
    - Project scaffolding
    - Test execution
    
    Skills:
    - start_dev_server: Start development server with hot reload
    - inspect_memory: Inspect memory layers
    - stream_events: Stream events in real-time
    - profile_operation: Profile performance
    - run_tests: Execute test suite
    - scaffold_project: Create new project from template
    
    Example:
        agent = DevExAgent(
            agent_id="devex",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """
        Initialize DevEx Agent.
        
        Args:
            agent_id: Agent identifier (should be 'devex')
            event_bus: Event bus for communication
            memory: Memory system instance
            **config: Additional configuration
        """
        self.config = config
        self._dev_server = None
        self._memory_inspector = MemoryInspector(memory)
        self._event_viewer = EventStreamViewer(event_bus)
        self._profiler = PerformanceProfiler()
        
        # Store for convenience
        global _event_bus
        _event_bus = event_bus
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] DevEx Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register DevEx Agent skills."""
        self.register_skill("start_dev_server", self.start_dev_server)
        self.register_skill("inspect_memory", self.inspect_memory)
        self.register_skill("stream_events", self.stream_events_skill)
        self.register_skill("profile_operation", self.profile_operation)
        self.register_skill("run_tests", self.run_tests)
        self.register_skill("scaffold_project", self.scaffold_project)
    
    async def start_dev_server(
        self,
        hot_reload: bool = True,
        port: int = 8000,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Start development server with hot reload.
        
        Args:
            hot_reload: Enable hot reload
            port: Server port
            debug: Debug mode
        
        Returns:
            Server status
        
        Example:
            result = await agent.start_dev_server(
                hot_reload=True,
                port=8000
            )
        """
        logger.info(
            f"[{self.agent_id}] Starting dev server "
            f"(hot_reload={hot_reload}, port={port})"
        )
        
        try:
            self._dev_server = DevServer(
                hot_reload=hot_reload,
                port=port,
                debug=debug
            )
            
            # Start in background (non-blocking)
            import asyncio
            asyncio.create_task(self._dev_server.start())
            
            # Give it time to initialize
            await asyncio.sleep(2)
            
            return {
                "status": "success",
                "message": f"Dev server started on port {port}",
                "hot_reload": hot_reload,
                "debug": debug
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to start dev server: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def inspect_memory(
        self,
        layer: str = "all",
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Inspect memory layers.
        
        Args:
            layer: Memory layer (session, working, longterm, all)
            session_id: Filter by session
            limit: Max results
        
        Returns:
            Memory entries
        
        Example:
            memory = await agent.inspect_memory(
                layer="working",
                session_id="session_123",
                limit=10
            )
        """
        logger.info(
            f"[{self.agent_id}] Inspecting memory "
            f"(layer={layer}, session_id={session_id})"
        )
        
        try:
            result = await self._memory_inspector.inspect(
                layer=layer,
                session_id=session_id,
                limit=limit
            )
            
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Memory inspection failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def stream_events_skill(
        self,
        filters: Optional[Dict[str, Any]] = None,
        duration: int = 30
    ) -> Dict[str, Any]:
        """
        Stream events in real-time.
        
        Args:
            filters: Event filters
            duration: Stream duration in seconds
        
        Returns:
            Streaming status
        
        Example:
            result = await agent.stream_events_skill(
                filters={"type": "agent.request"},
                duration=60
            )
        """
        logger.info(f"[{self.agent_id}] Starting event stream (duration={duration}s)")
        
        try:
            import asyncio
            
            # Start streaming in background
            stream_task = asyncio.create_task(
                self._event_viewer.stream(filters=filters)
            )
            
            # Let it run for specified duration
            await asyncio.sleep(duration)
            
            # Stop streaming
            self._event_viewer.stop()
            
            return {
                "status": "success",
                "message": f"Streamed events for {duration} seconds"
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Event streaming failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def profile_operation(
        self,
        component: str,
        operation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Profile an operation's performance.
        
        Args:
            component: Component name
            operation_params: Operation to profile
        
        Returns:
            Profiling results
        
        Example:
            profile = await agent.profile_operation(
                component="memory",
                operation_params={"operation": "write", "count": 100}
            )
        """
        logger.info(f"[{self.agent_id}] Profiling operation: {component}")
        
        # This is a placeholder - actual implementation would
        # call the operation and measure performance
        
        async def mock_operation():
            import asyncio
            await asyncio.sleep(0.1)  # Simulate work
        
        try:
            profile_data = await self._profiler.profile(
                component=component,
                operation=mock_operation
            )
            
            return {
                "status": "success",
                "profile": profile_data
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Profiling failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_tests(
        self,
        suite: Optional[str] = None,
        coverage: bool = True,
        markers: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run test suite.
        
        Args:
            suite: Test suite name
            coverage: Generate coverage
            markers: Pytest markers
        
        Returns:
            Test results
        
        Example:
            results = await agent.run_tests(
                suite="memory",
                coverage=True
            )
        """
        logger.info(f"[{self.agent_id}] Running tests (suite={suite})")
        
        try:
            from agents.devex.test_runner import run_tests_cli
            
            results = await run_tests_cli(
                suite=suite,
                coverage=coverage,
                markers=markers
            )
            
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
    
    async def scaffold_project(
        self,
        name: str,
        template_type: str = "agent",
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new project from template.
        
        Args:
            name: Project name
            template_type: Template (agent, project, skill)
            target_path: Target directory
        
        Returns:
            Scaffolding result
        
        Example:
            result = await agent.scaffold_project(
                name="my-agent",
                template_type="agent"
            )
        """
        logger.info(
            f"[{self.agent_id}] Scaffolding project "
            f"(name={name}, type={template_type})"
        )
        
        try:
            from agents.devex.project_scaffold import create_from_template
            from pathlib import Path
            
            result = create_from_template(
                name=name,
                template_type=template_type,
                target_path=Path(target_path) if target_path else Path.cwd()
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Scaffolding failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


# Global event bus reference for db_operations and other modules
_event_bus = None

def get_event_bus():
    """Get global event bus instance."""
    return _event_bus


# Entry point for running agent standalone
if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    asyncio.run(run_agent(DevExAgent, "devex"))
