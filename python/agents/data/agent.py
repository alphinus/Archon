"""
Data & Mock Agent

Main agent class that coordinates mock data generation, database seeding,
and test scenario creation for Archon.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from agents.data.mock_generator import MockDataGenerator
from agents.data.seed_scripts import DatabaseSeeder
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataMockAgent(BaseAgent):
    """
    Data & Mock Agent for Archon.
    
    Provides skills for:
    - Mock data generation (users, sessions, memory, events, etc.)
    - Database seeding (PostgreSQL, Redis)
    - Test scenario creation
    - Data validation
    
    Skills:
    - generate_mock_data: Generate mock data for specific entity type
    - seed_database: Seed database with test data
    - create_scenario: Create test scenario
    - validate_data: Validate data integrity
    
    Example:
        agent = DataMockAgent(
            agent_id="data",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """
        Initialize Data & Mock Agent.
        
        Args:
            agent_id: Agent identifier (should be 'data')
            event_bus: Event bus for communication
            memory: Memory system instance
            **config: Additional configuration (db_url, redis_url, etc.)
        """
        self.mock_generator = MockDataGenerator()
        self.db_seeder = None
        
        # Store config for lazy initialization
        self.config = config
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] Data & Mock Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register Data & Mock Agent skills."""
        self.register_skill("generate_mock_data", self.generate_mock_data)
        self.register_skill("seed_database", self.seed_database)
        self.register_skill("create_scenario", self.create_scenario)
        self.register_skill("validate_data", self.validate_data)
        self.register_skill("generate_full_dataset", self.generate_full_dataset)
    
    async def generate_mock_data(
        self,
        entity_type: str,
        count: int = 10,
        **params
    ) -> Dict[str, Any]:
        """
        Generate mock data for specified entity type.
        
        Args:
            entity_type: Type of entity (users, sessions, memory, events, etc.)
            count: Number of entities to generate
            **params: Additional parameters (user_ids, session_ids, etc.)
        
        Returns:
            Dictionary with generated data and metadata
        
        Example:
            result = await agent.generate_mock_data(
                entity_type="users",
                count=5
            )
            # result = {"data": [...], "count": 5, "entity_type": "users"}
        """
        logger.info(
            f"[{self.agent_id}] Generating {count} {entity_type}"
        )
        
        generators = {
            "users": lambda: self.mock_generator.generate_users(count),
            "sessions": lambda: self.mock_generator.generate_sessions(
                user_ids=params.get("user_ids", []),
                count=count
            ),
            "memory": lambda: self.mock_generator.generate_memory_entries(
                session_ids=params.get("session_ids", []),
                layer=params.get("layer", "working"),
                count=count
            ),
            "events": lambda: self.mock_generator.generate_events(
                session_ids=params.get("session_ids", []),
                count=count
            ),
            "work_orders": lambda: self.mock_generator.generate_work_orders(
                session_ids=params.get("session_ids", []),
                count=count
            ),
            "knowledge": lambda: self.mock_generator.generate_knowledge_entries(count),
            "projects": lambda: self.mock_generator.generate_projects(
                user_ids=params.get("user_ids", []),
                count=count
            )
        }
        
        if entity_type not in generators:
            raise ValueError(
                f"Unknown entity type: {entity_type}. "
                f"Supported: {list(generators.keys())}"
            )
        
        data = generators[entity_type]()
        
        return {
            "data": data,
            "count": len(data),
            "entity_type": entity_type,
            "generated_at": self._timestamp()
        }
    
    async def seed_database(
        self,
        environment: str = "dev",
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Seed database with test data.
        
        Args:
            environment: Environment name (dev, staging, prod)
            clear_existing: Whether to clear existing data first
        
        Returns:
            Dictionary with seeding results
        
        Example:
            result = await agent.seed_database(
                environment="dev",
                clear_existing=True
            )
        """
        logger.info(
            f"[{self.agent_id}] Seeding database for {environment} "
            f"(clear_existing={clear_existing})"
        )
        
        # Initialize seeder if needed
        if not self.db_seeder:
            self.db_seeder = DatabaseSeeder(
                db_url=self.config.get("db_url", "postgresql://localhost/archon"),
                redis_url=self.config.get("redis_url", "redis://localhost:6379"),
                mock_generator=self.mock_generator
            )
        
        try:
            counts = await self.db_seeder.seed_all(
                environment=environment,
                clear_existing=clear_existing
            )
            
            return {
                "status": "success",
                "environment": environment,
                "counts": counts,
                "total_records": sum(counts.values()),
                "seeded_at": self._timestamp()
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Seeding failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "seeded_at": self._timestamp()
            }
    
    async def create_scenario(
        self,
        scenario_type: str,
        **params
    ) -> Dict[str, Any]:
        """
        Create test scenario.
        
        Args:
            scenario_type: Scenario type (happy_path, error, edge_case, load, chaos)
            **params: Scenario-specific parameters
        
        Returns:
            Scenario configuration and data
        
        Example:
            scenario = await agent.create_scenario(
                scenario_type="happy_path",
                workflow="agent_creation"
            )
        """
        logger.info(
            f"[{self.agent_id}] Creating scenario: {scenario_type}"
        )
        
        scenarios = {
            "happy_path": self._create_happy_path_scenario,
            "error": self._create_error_scenario,
            "edge_case": self._create_edge_case_scenario,
            "load": self._create_load_scenario,
            "chaos": self._create_chaos_scenario
        }
        
        if scenario_type not in scenarios:
            raise ValueError(
                f"Unknown scenario type: {scenario_type}. "
                f"Supported: {list(scenarios.keys())}"
            )
        
        scenario_data = await scenarios[scenario_type](**params)
        
        return {
            "scenario_type": scenario_type,
            "data": scenario_data,
            "created_at": self._timestamp()
        }
    
    async def validate_data(
        self,
        scope: str = "all"
    ) -> Dict[str, Any]:
        """
        Validate data integrity.
        
        Args:
            scope: Validation scope (all, users, sessions, etc.)
        
        Returns:
            Validation results
        
        Example:
            result = await agent.validate_data(scope="all")
        """
        logger.info(f"[{self.agent_id}] Validating data: {scope}")
        
        # Placeholder - implement actual validation logic
        return {
            "status": "success",
            "scope": scope,
            "issues": [],
            "validated_at": self._timestamp()
        }
    
    async def generate_full_dataset(
        self,
        num_users: int = 10,
        num_sessions: int = 20,
        num_events: int = 100
    ) -> Dict[str, Any]:
        """
        Generate complete dataset with all entity types.
        
        Args:
            num_users: Number of users
            num_sessions: Number of sessions
            num_events: Number of events
        
        Returns:
            Full dataset
        
        Example:
            dataset = await agent.generate_full_dataset(
                num_users=5,
                num_sessions=10,
                num_events=50
            )
        """
        logger.info(
            f"[{self.agent_id}] Generating full dataset "
            f"(users={num_users}, sessions={num_sessions}, events={num_events})"
        )
        
        dataset = self.mock_generator.generate_full_dataset(
            num_users=num_users,
            num_sessions=num_sessions,
            num_events=num_events
        )
        
        return {
            "dataset": dataset,
            "summary": {
                entity_type: len(data)
                for entity_type, data in dataset.items()
            },
            "generated_at": self._timestamp()
        }
    
    # Scenario creation helpers
    
    async def _create_happy_path_scenario(self, **params) -> Dict[str, Any]:
        """Create happy path test scenario."""
        return {
            "description": "Happy path workflow",
            "steps": [
                {"action": "create_user", "expected": "success"},
                {"action": "create_session", "expected": "success"},
                {"action": "execute_task", "expected": "success"},
                {"action": "verify_result", "expected": "success"}
            ],
            "data": self.mock_generator.generate_full_dataset(
                num_users=1,
                num_sessions=1,
                num_events=10
            )
        }
    
    async def _create_error_scenario(self, **params) -> Dict[str, Any]:
        """Create error handling test scenario."""
        return {
            "description": "Error handling workflow",
            "steps": [
                {"action": "invalid_input", "expected": "error"},
                {"action": "missing_dependency", "expected": "error"},
                {"action": "timeout", "expected": "error"}
            ],
            "errors": [
                {"type": "validation_error", "message": "Invalid input"},
                {"type": "dependency_error", "message": "Service unavailable"},
                {"type": "timeout_error", "message": "Operation timeout"}
            ]
        }
    
    async def _create_edge_case_scenario(self, **params) -> Dict[str, Any]:
        """Create edge case test scenario."""
        return {
            "description": "Edge case scenarios",
            "cases": [
                {"name": "empty_input", "data": {}},
                {"name": "max_limits", "data": {"count": 10000}},
                {"name": "special_characters", "data": {"text": "!@#$%^&*()"}},
                {"name": "unicode", "data": {"text": "こんにちは"}}
            ]
        }
    
    async def _create_load_scenario(self, **params) -> Dict[str, Any]:
        """Create load testing scenario."""
        load_level = params.get("load_level", "medium")
        
        levels = {
            "low": {"users": 10, "sessions": 50, "events": 500},
            "medium": {"users": 50, "sessions": 200, "events": 2000},
            "high": {"users": 100, "sessions": 1000, "events": 10000}
        }
        
        config = levels.get(load_level, levels["medium"])
        
        return {
            "description": f"Load testing ({load_level})",
            "load_level": load_level,
            "config": config,
            "data": self.mock_generator.generate_full_dataset(**config)
        }
    
    async def _create_chaos_scenario(self, **params) -> Dict[str, Any]:
        """Create chaos testing scenario."""
        return {
            "description": "Chaos engineering scenario",
            "chaos_actions": [
                {"type": "redis_failure", "duration": 30},
                {"type": "postgres_failure", "duration": 30},
                {"type": "network_latency", "latency_ms": 500},
                {"type": "cpu_pressure", "percentage": 80},
                {"type": "memory_pressure", "percentage": 90}
            ],
            "expected_behavior": "graceful_degradation"
        }
    
    def _timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Entry point for running agent standalone
if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    # Pass config from env vars if needed, but run_agent handles basic infra
    asyncio.run(run_agent(DataMockAgent, "data"))
