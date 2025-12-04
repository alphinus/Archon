"""
Database Seeding for Archon

Provides idempotent database seeding for different environments.
Populates Postgres and Redis with test data.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """
    Seeds Archon database with mock data.
    
    Supports:
    - PostgreSQL seeding
    - Redis cache population
    - Memory system initialization
    - Idempotent operations (safe to run multiple times)
    - Environment-specific seeds (dev, staging, prod)
    
    Example:
        seeder = DatabaseSeeder(db_url="postgresql://...", redis_url="redis://...")
        await seeder.seed_all(environment="dev")
    """
    
    def __init__(
        self,
        db_url: str,
        redis_url: str,
        mock_generator: Any = None
    ):
        """
        Initialize seeder.
        
        Args:
            db_url: PostgreSQL connection URL
            redis_url: Redis connection URL
            mock_generator: MockDataGenerator instance (optional)
        """
        self.db_url = db_url
        self.redis_url = redis_url
        
        # Import here to avoid circular dependencies
        from agents.data.mock_generator import MockDataGenerator
        self.generator = mock_generator or MockDataGenerator()
        
        self.db = None
        self.redis = None
    
    async def connect(self) -> None:
        """Establish database connections."""
        import asyncpg
        import aioredis
        
        self.db = await asyncpg.connect(self.db_url)
        self.redis = await aioredis.from_url(self.redis_url)
        
        logger.info("Connected to database and Redis")
    
    async def disconnect(self) -> None:
        """Close database connections."""
        if self.db:
            await self.db.close()
        if self.redis:
            await self.redis.close()
        
        logger.info("Disconnected from database and Redis")
    
    async def seed_all(
        self,
        environment: str = "dev",
        clear_existing: bool = False
    ) -> Dict[str, int]:
        """
        Seed all data for specified environment.
        
        Args:
            environment: Environment name (dev, staging, prod)
            clear_existing: Whether to clear existing data first
        
        Returns:
            Dictionary with counts of seeded records
        
        Example:
            counts = await seeder.seed_all(environment="dev", clear_existing=True)
            print(f"Seeded {counts['users']} users")
        """
        await self.connect()
        
        try:
            if clear_existing:
                await self._clear_data()
            
            # Generate environment-specific volume
            volumes = {
                "dev": {"users": 5, "sessions": 10, "events": 50},
                "staging": {"users": 20, "sessions": 50, "events": 200},
                "prod": {"users": 100, "sessions": 500, "events": 2000}
            }
            
            config = volumes.get(environment, volumes["dev"])
            
            # Generate full dataset
            dataset = self.generator.generate_full_dataset(
                num_users=config["users"],
                num_sessions=config["sessions"],
                num_events=config["events"]
            )
            
            # Seed each table
            counts = {}
            counts["users"] = await self._seed_users(dataset["users"])
            counts["sessions"] = await self._seed_sessions(dataset["sessions"])
            counts["memory"] = await self._seed_memory(
                dataset["memory_session"] +
                dataset["memory_working"] +
                dataset["memory_longterm"]
            )
            counts["events"] = await self._seed_events(dataset["events"])
            counts["work_orders"] = await self._seed_work_orders(dataset["work_orders"])
            counts["knowledge"] = await self._seed_knowledge(dataset["knowledge"])
            counts["projects"] = await self._seed_projects(dataset["projects"])
            
            # Populate Redis cache
            await self._populate_redis_cache(dataset)
            
            logger.info(
                f"Seeding complete for {environment} environment: {counts}"
            )
            
            return counts
            
        finally:
            await self.disconnect()
    
    async def _clear_data(self) -> None:
        """Clear all existing data (use with caution!)."""
        tables = [
            "projects", "knowledge", "work_orders", 
            "events", "memory", "sessions", "users"
        ]
        
        for table in tables:
            await self.db.execute(f"TRUNCATE TABLE {table} CASCADE")
        
        await self.redis.flushdb()
        
        logger.warning("Cleared all existing data")
    
    async def _seed_users(self, users: List[Dict[str, Any]]) -> int:
        """Seed users table."""
        count = 0
        for user in users:
            try:
                await self.db.execute(
                    """
                    INSERT INTO users (id, name, email, created_at, preferences)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    user["id"],
                    user["name"],
                    user["email"],
                    user["created_at"],
                    user["preferences"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding user {user['id']}: {e}")
        
        logger.info(f"Seeded {count} users")
        return count
    
    async def _seed_sessions(self, sessions: List[Dict[str, Any]]) -> int:
        """Seed sessions table."""
        count = 0
        for session in sessions:
            try:
                await self.db.execute(
                    """
                    INSERT INTO sessions (id, user_id, agent_type, status, created_at, updated_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    session["id"],
                    session["user_id"],
                    session["agent_type"],
                    session["status"],
                    session["created_at"],
                    session["updated_at"],
                    session["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding session {session['id']}: {e}")
        
        logger.info(f"Seeded {count} sessions")
        return count
    
    async def _seed_memory(self, entries: List[Dict[str, Any]]) -> int:
        """Seed memory table."""
        count = 0
        for entry in entries:
            try:
                await self.db.execute(
                    """
                    INSERT INTO memory (id, session_id, layer, key, value, created_at, ttl, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    entry["id"],
                    entry["session_id"],
                    entry["layer"],
                    entry["key"],
                    entry["value"],
                    entry["created_at"],
                    entry["ttl"],
                    entry["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding memory entry {entry['id']}: {e}")
        
        logger.info(f"Seeded {count} memory entries")
        return count
    
    async def _seed_events(self, events: List[Dict[str, Any]]) -> int:
        """Seed events table."""
        count = 0
        for event in events:
            try:
                await self.db.execute(
                    """
                    INSERT INTO events (id, type, session_id, timestamp, payload, severity, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    event["id"],
                    event["type"],
                    event["session_id"],
                    event["timestamp"],
                    event["payload"],
                    event["severity"],
                    event["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding event {event['id']}: {e}")
        
        logger.info(f"Seeded {count} events")
        return count
    
    async def _seed_work_orders(self, work_orders: List[Dict[str, Any]]) -> int:
        """Seed work_orders table."""
        count = 0
        for wo in work_orders:
            try:
                await self.db.execute(
                    """
                    INSERT INTO work_orders (id, session_id, title, description, status, priority, created_at, updated_at, assigned_to, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    wo["id"],
                    wo["session_id"],
                    wo["title"],
                    wo["description"],
                    wo["status"],
                    wo["priority"],
                    wo["created_at"],
                    wo["updated_at"],
                    wo["assigned_to"],
                    wo["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding work order {wo['id']}: {e}")
        
        logger.info(f"Seeded {count} work orders")
        return count
    
    async def _seed_knowledge(self, entries: List[Dict[str, Any]]) -> int:
        """Seed knowledge base table."""
        count = 0
        for entry in entries:
            try:
                await self.db.execute(
                    """
                    INSERT INTO knowledge (id, title, content, category, tags, created_at, updated_at, author, views, useful_votes, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    entry["id"],
                    entry["title"],
                    entry["content"],
                    entry["category"],
                    entry["tags"],
                    entry["created_at"],
                    entry["updated_at"],
                    entry["author"],
                    entry["views"],
                    entry["useful_votes"],
                    entry["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding knowledge entry {entry['id']}: {e}")
        
        logger.info(f"Seeded {count} knowledge entries")
        return count
    
    async def _seed_projects(self, projects: List[Dict[str, Any]]) -> int:
        """Seed projects table."""
        count = 0
        for project in projects:
            try:
                await self.db.execute(
                    """
                    INSERT INTO projects (id, name, description, owner_id, status, created_at, updated_at, agents, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    project["id"],
                    project["name"],
                    project["description"],
                    project["owner_id"],
                    project["status"],
                    project["created_at"],
                    project["updated_at"],
                    project["agents"],
                    project["metadata"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Error seeding project {project['id']}: {e}")
        
        logger.info(f"Seeded {count} projects")
        return count
    
    async def _populate_redis_cache(self, dataset: Dict[str, Any]) -> None:
        """Populate Redis cache with frequently accessed data."""
        # Cache active sessions
        active_sessions = [
            s for s in dataset["sessions"]
            if s["status"] == "active"
        ]
        for session in active_sessions:
            await self.redis.setex(
                f"session:{session['id']}",
                3600,  # 1 hour TTL
                str(session)
            )
        
        # Cache session memory
        for entry in dataset["memory_session"]:
            await self.redis.setex(
                f"memory:session:{entry['session_id']}:{entry['key']}",
                entry.get("ttl", 300),
                str(entry["value"])
            )
        
        logger.info("Populated Redis cache")
