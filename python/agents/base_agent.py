"""
Base Agent Infrastructure for Archon Multi-Agent System

This module provides the foundational BaseAgent class that all specialized
agents inherit from. It handles event communication, memory management,
and skill registration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all Archon agents.
    
    All specialized agents (Testing, DevEx, UI, Documentation, Orchestration,
    Infrastructure, Data & Mock) inherit from this class to get standardized
    event handling, memory access, and skill management.
    
    Attributes:
        agent_id: Unique identifier for this agent
        event_bus: Event bus for inter-agent communication
        memory: Access to 4-layer memory system
        skills: Registry of callable skills this agent provides
    
    Example:
        class TestingAgent(BaseAgent):
            def _setup_skills(self):
                self.register_skill('run_tests', self.run_tests)
            
            async def run_tests(self, test_suite: str, coverage: bool = True):
                # Implementation
                pass
    """
    
    def __init__(
        self,
        agent_id: str,
        event_bus: Any,  # EventBus type from archon.core.events
        memory: Any,     # MemorySystem type from archon.memory
    ):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier (e.g., 'testing', 'devex')
            event_bus: EventBus instance for pub/sub communication
            memory: MemorySystem instance for state management
        """
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.memory = memory
        self.skills: Dict[str, Callable] = {}
        self._running = False
        
        # Setup agent-specific skills
        self._setup_skills()
        
        logger.info(
            f"[{self.agent_id}] Agent initialized with {len(self.skills)} skills"
        )
    
    @abstractmethod
    def _setup_skills(self) -> None:
        """
        Register agent-specific skills.
        
        Each agent implementation should override this method to register
        their specific skills using self.register_skill().
        
        Example:
            def _setup_skills(self):
                self.register_skill('my_skill', self.my_skill_handler)
        """
        pass
    
    def register_skill(self, skill_name: str, handler: Callable) -> None:
        """
        Register a skill handler.
        
        Args:
            skill_name: Name of the skill (used in event requests)
            handler: Async callable that implements the skill
        
        Example:
            self.register_skill('generate_mock_data', self.generate_mock_data)
        """
        self.skills[skill_name] = handler
        logger.debug(f"[{self.agent_id}] Registered skill: {skill_name}")
    
    async def start(self) -> None:
        """
        Start the agent and subscribe to events.
        
        This sets up event subscriptions for:
        - agent.{agent_id}.request - Skill execution requests
        - agent.{agent_id}.status - Status queries
        - agent.broadcast - System-wide broadcasts
        """
        self._running = True
        
        # Subscribe to agent-specific requests
        await self.event_bus.subscribe(
            f"agent.{self.agent_id}.request",
            self._handle_request
        )
        
        # Subscribe to status queries
        await self.event_bus.subscribe(
            f"agent.{self.agent_id}.status",
            self._handle_status_query
        )
        
        # Subscribe to broadcasts
        await self.event_bus.subscribe(
            "agent.broadcast",
            self._handle_broadcast
        )
        
        # Publish startup event
        await self._publish_status("started", {"skills": list(self.skills.keys())})
        
        logger.info(
            f"[{self.agent_id}] Agent started and listening for events"
        )
    
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self._running = False
        await self._publish_status("stopped", {})
        logger.info(f"[{self.agent_id}] Agent stopped")
    
    async def _handle_request(self, event: Dict[str, Any]) -> None:
        """
        Handle incoming skill execution requests.
        
        Event format:
        {
            "correlation_id": "unique-id",
            "skill": "skill_name",
            "params": {...},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        Args:
            event: Event data containing skill name and parameters
        """
        correlation_id = event.get("correlation_id", "unknown")
        skill_name = event.get("skill")
        params = event.get("params", {})
        
        logger.info(
            f"[{self.agent_id}] Received request for skill '{skill_name}' "
            f"(correlation_id: {correlation_id})"
        )
        
        try:
            if skill_name not in self.skills:
                raise ValueError(f"Unknown skill: {skill_name}")
            
            # Execute skill
            handler = self.skills[skill_name]
            result = await handler(**params)
            
            # Publish success response
            await self._publish_response(correlation_id, result)
            
            logger.info(
                f"[{self.agent_id}] Successfully executed '{skill_name}'"
            )
            
        except Exception as e:
            # Publish error response
            await self._publish_error(correlation_id, str(e))
            
            logger.error(
                f"[{self.agent_id}] Error executing '{skill_name}': {e}",
                exc_info=True
            )
    
    async def _handle_status_query(self, event: Dict[str, Any]) -> None:
        """
        Handle status queries.
        
        Args:
            event: Status query event
        """
        correlation_id = event.get("correlation_id", "unknown")
        
        status = {
            "agent_id": self.agent_id,
            "running": self._running,
            "skills": list(self.skills.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._publish_response(correlation_id, status)
    
    async def _handle_broadcast(self, event: Dict[str, Any]) -> None:
        """
        Handle broadcast events.
        
        Override this in subclasses to handle system-wide broadcasts.
        
        Args:
            event: Broadcast event data
        """
        logger.debug(
            f"[{self.agent_id}] Received broadcast: {event.get('message')}"
        )
    
    async def _publish_response(
        self,
        correlation_id: str,
        result: Any
    ) -> None:
        """
        Publish a success response event.
        
        Args:
            correlation_id: ID to correlate request/response
            result: Result data from skill execution
        """
        await self.event_bus.publish(
            f"agent.{self.agent_id}.response",
            {
                "correlation_id": correlation_id,
                "result": result,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _publish_error(
        self,
        correlation_id: str,
        error: str
    ) -> None:
        """
        Publish an error response event.
        
        Args:
            correlation_id: ID to correlate request/response
            error: Error message
        """
        await self.event_bus.publish(
            f"agent.{self.agent_id}.error",
            {
                "correlation_id": correlation_id,
                "error": error,
                "status": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _publish_status(
        self,
        status: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Publish agent status update.
        
        Args:
            status: Status string (e.g., 'started', 'stopped', 'busy')
            details: Additional status details
        """
        await self.event_bus.publish(
            f"agent.{self.agent_id}.status",
            {
                "agent_id": self.agent_id,
                "status": status,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def call_skill(
        self,
        target_agent: str,
        skill: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Any:
        """
        Call a skill on another agent.
        
        This is a helper method for inter-agent communication. It publishes
        a request event and waits for the response.
        
        Args:
            target_agent: Agent ID to call (e.g., 'data', 'testing')
            skill: Skill name to execute
            params: Skill parameters
            timeout: Max wait time in seconds
        
        Returns:
            Result from the skill execution
        
        Raises:
            TimeoutError: If response not received within timeout
            ValueError: If target agent returns an error
        
        Example:
            result = await self.call_skill(
                'data',
                'generate_mock_data',
                {'type': 'user', 'count': 10}
            )
        """
        import uuid
        
        correlation_id = str(uuid.uuid4())
        params = params or {}
        
        # Create a future to wait for response
        response_future = asyncio.Future()
        
        # Subscribe to response
        async def handle_response(event: Dict[str, Any]) -> None:
            if event.get("correlation_id") == correlation_id:
                if event.get("status") == "success":
                    response_future.set_result(event.get("result"))
                else:
                    response_future.set_exception(
                        ValueError(event.get("error", "Unknown error"))
                    )
        
        await self.event_bus.subscribe(
            f"agent.{target_agent}.response",
            handle_response
        )
        
        await self.event_bus.subscribe(
            f"agent.{target_agent}.error",
            handle_response
        )
        
        # Publish request
        await self.event_bus.publish(
            f"agent.{target_agent}.request",
            {
                "correlation_id": correlation_id,
                "skill": skill,
                "params": params,
                "source_agent": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.debug(
            f"[{self.agent_id}] Called {target_agent}.{skill} "
            f"(correlation_id: {correlation_id})"
        )
        
        # Wait for response with timeout
        try:
            result = await asyncio.wait_for(response_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Timeout waiting for {target_agent}.{skill} response"
            )


async def run_agent(agent_class, agent_id: str, **kwargs) -> None:
    """
    Run an agent indefinitely.
    
    Args:
        agent_class: Agent class to instantiate
        agent_id: Agent identifier
        **kwargs: Additional arguments for agent constructor
    """
    import os
    import signal
    
    # Try to import infrastructure
    try:
        from src.events.bus import EventBus
        # from src.memory.system import MemorySystem  # Not available yet
    except ImportError:
        # Fallback for standalone testing without src package
        logger.warning("Could not import src.events.bus, using mocks")
        
        class MockEventBus:
            async def connect(self): pass
            async def disconnect(self): pass
            async def subscribe(self, topic, handler): pass
            async def publish(self, topic, event): logger.info(f"Mock publish: {topic}")
            
        EventBus = MockEventBus
    
    # Config
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/archon")
    event_bus_url = os.getenv("EVENT_BUS_URL", redis_url)
    
    # Initialize infrastructure
    logger.info(f"Connecting to Event Bus at {event_bus_url}")
    try:
        event_bus = EventBus(event_bus_url)
        await event_bus.connect()
    except TypeError:
        # Handle mock or different signature
        event_bus = EventBus()
        await event_bus.connect()
    
    # Initialize memory (placeholder for now)
    memory = None
    
    # Initialize agent
    agent = agent_class(
        agent_id=agent_id,
        event_bus=event_bus,
        memory=memory,
        **kwargs
    )
    
    await agent.start()
    
    # Handle shutdown signals
    stop_event = asyncio.Event()
    
    def handle_signal():
        logger.info("Received shutdown signal")
        stop_event.set()
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Windows or non-main thread
            pass
    
    logger.info(f"Agent {agent_id} running. Press Ctrl+C to stop.")
    
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down...")
        await agent.stop()
        if hasattr(event_bus, "disconnect"):
            await event_bus.disconnect()

