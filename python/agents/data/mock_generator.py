"""
Mock Data Generator for Archon

Generates realistic test data for all Archon components using Faker.
Supports configurable data volumes and maintains referential integrity.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import uuid
from faker import Faker

fake = Faker()


class MockDataGenerator:
    """
    Generates realistic mock data for testing Archon components.
    
    Supports:
    - User profiles
    - Agent sessions
    - Memory entries (Session, Working, Long-Term)
    - Events
    - Work orders
    - Knowledge base entries
    - Projects
    
    Example:
        generator = MockDataGenerator()
        users = generator.generate_users(count=10)
        sessions = generator.generate_sessions(user_ids=[u['id'] for u in users])
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator.
        
        Args:
            seed: Random seed for reproducible data (optional)
        """
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        
        self.faker = Faker()
    
    def generate_users(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock user profiles.
        
        Args:
            count: Number of users to generate
        
        Returns:
            List of user dictionaries with realistic data
        
        Example:
            users = generator.generate_users(count=5)
            # [{'id': 'usr_123', 'name': 'John Doe', ...}, ...]
        """
        users = []
        for _ in range(count):
            user = {
                "id": f"usr_{uuid.uuid4().hex[:12]}",
                "name": self.faker.name(),
                "email": self.faker.email(),
                "created_at": self._random_datetime(days_ago=365).isoformat(),
                "preferences": {
                    "theme": random.choice(["light", "dark", "auto"]),
                    "notifications": random.choice([True, False]),
                    "language": random.choice(["en", "de", "fr", "es"])
                }
            }
            users.append(user)
        return users
    
    def generate_sessions(
        self,
        user_ids: List[str],
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate mock agent sessions.
        
        Args:
            user_ids: List of user IDs to assign sessions to
            count: Number of sessions to generate
        
        Returns:
            List of session dictionaries
        """
        sessions = []
        for _ in range(count):
            session_id = str(uuid.uuid4())
            user_id = random.choice(user_ids)
            created_at = self._random_datetime(days_ago=30)
            
            session = {
                "id": session_id,
                "user_id": user_id,
                "agent_type": random.choice([
                    "code_generator",
                    "data_analyst",
                    "content_writer",
                    "debugger"
                ]),
                "status": random.choice(["active", "completed", "paused", "failed"]),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(
                    minutes=random.randint(1, 120)
                )).isoformat(),
                "metadata": {
                    "goal": self.faker.sentence(),
                    "tags": [self.faker.word() for _ in range(random.randint(1, 5))]
                }
            }
            sessions.append(session)
        return sessions
    
    def generate_memory_entries(
        self,
        session_ids: List[str],
        layer: str = "working",
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Generate mock memory entries for a specific layer.
        
        Args:
            session_ids: List of session IDs
            layer: Memory layer ('session', 'working', 'longterm')
            count: Number of entries to generate
        
        Returns:
            List of memory entry dictionaries
        """
        entries = []
        for _ in range(count):
            entry = {
                "id": str(uuid.uuid4()),
                "session_id": random.choice(session_ids),
                "layer": layer,
                "key": f"{self.faker.word()}_{random.randint(1, 999)}",
                "value": self._generate_memory_value(),
                "created_at": self._random_datetime(days_ago=7).isoformat(),
                "ttl": random.choice([None, 300, 3600, 86400]) if layer == "session" else None,
                "metadata": {
                    "source": random.choice(["user_input", "agent", "system"]),
                    "importance": random.uniform(0, 1),
                    "tags": [self.faker.word() for _ in range(random.randint(0, 3))]
                }
            }
            entries.append(entry)
        return entries
    
    def generate_events(
        self,
        session_ids: List[str],
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Generate mock system events.
        
        Args:
            session_ids: List of session IDs
            count: Number of events to generate
        
        Returns:
            List of event dictionaries
        """
        event_types = [
            "agent.started",
            "agent.stopped",
            "memory.created",
            "memory.updated",
            "memory.deleted",
            "task.created",
            "task.completed",
            "task.failed",
            "error.occurred",
            "warning.issued"
        ]
        
        events = []
        for _ in range(count):
            event = {
                "id": str(uuid.uuid4()),
                "type": random.choice(event_types),
                "session_id": random.choice(session_ids),
                "timestamp": self._random_datetime(days_ago=7).isoformat(),
                "payload": {
                    "message": self.faker.sentence(),
                    "details": {
                        "key1": self.faker.word(),
                        "key2": random.randint(1, 100)
                    }
                },
                "severity": random.choice(["debug", "info", "warning", "error"]),
                "metadata": {
                    "source": random.choice(["agent", "system", "user"]),
                    "environment": random.choice(["dev", "staging", "prod"])
                }
            }
            events.append(event)
        return events
    
    def generate_work_orders(
        self,
        session_ids: List[str],
        count: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Generate mock work orders.
        
        Args:
            session_ids: List of session IDs
            count: Number of work orders to generate
        
        Returns:
            List of work order dictionaries
        """
        work_orders = []
        for _ in range(count):
            created_at = self._random_datetime(days_ago=14)
            
            work_order = {
                "id": f"wo_{uuid.uuid4().hex[:12]}",
                "session_id": random.choice(session_ids),
                "title": self.faker.sentence(nb_words=6),
                "description": self.faker.paragraph(nb_sentences=3),
                "status": random.choice([
                    "pending", "in_progress", "completed", "failed", "cancelled"
                ]),
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(
                    hours=random.randint(1, 72)
                )).isoformat(),
                "assigned_to": random.choice([
                    "testing_agent",
                    "devex_agent",
                    "orchestration_agent",
                    None
                ]),
                "metadata": {
                    "estimated_duration": random.randint(5, 120),  # minutes
                    "tags": [self.faker.word() for _ in range(random.randint(1, 4))],
                    "dependencies": []
                }
            }
            work_orders.append(work_order)
        return work_orders
    
    def generate_knowledge_entries(
        self,
        count: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Generate mock knowledge base entries.
        
        Args:
            count: Number of entries to generate
        
        Returns:
            List of knowledge entry dictionaries
        """
        categories = ["tutorial", "api_reference", "guide", "faq", "troubleshooting"]
        
        entries = []
        for _ in range(count):
            entry = {
                "id": f"kb_{uuid.uuid4().hex[:12]}",
                "title": self.faker.sentence(nb_words=5),
                "content": self.faker.text(max_nb_chars=500),
                "category": random.choice(categories),
                "tags": [self.faker.word() for _ in range(random.randint(2, 6))],
                "created_at": self._random_datetime(days_ago=90).isoformat(),
                "updated_at": self._random_datetime(days_ago=30).isoformat(),
                "author": self.faker.name(),
                "views": random.randint(0, 1000),
                "useful_votes": random.randint(0, 100),
                "metadata": {
                    "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
                    "estimated_read_time": random.randint(2, 15)  # minutes
                }
            }
            entries.append(entry)
        return entries
    
    def generate_projects(
        self,
        user_ids: List[str],
        count: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Generate mock projects.
        
        Args:
            user_ids: List of user IDs
            count: Number of projects to generate
        
        Returns:
            List of project dictionaries
        """
        projects = []
        for _ in range(count):
            created_at = self._random_datetime(days_ago=180)
            
            project = {
                "id": f"proj_{uuid.uuid4().hex[:12]}",
                "name": self.faker.catch_phrase(),
                "description": self.faker.paragraph(nb_sentences=2),
                "owner_id": random.choice(user_ids),
                "status": random.choice(["planning", "active", "paused", "completed"]),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(
                    days=random.randint(1, 90)
                )).isoformat(),
                "agents": [
                    {
                        "agent_id": f"agent_{i}",
                        "role": random.choice(["primary", "support", "monitor"])
                    }
                    for i in range(random.randint(1, 5))
                ],
                "metadata": {
                    "repository": f"https://github.com/{self.faker.user_name()}/{self.faker.word()}",
                    "tech_stack": random.sample([
                        "Python", "TypeScript", "React", "PostgreSQL", 
                        "Redis", "Docker", "FastAPI"
                    ], k=random.randint(2, 5)),
                    "budget": random.randint(1000, 50000)
                }
            }
            projects.append(project)
        return projects
    
    def generate_full_dataset(
        self,
        num_users: int = 10,
        num_sessions: int = 20,
        num_events: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a complete dataset with all entity types.
        
        Args:
            num_users: Number of users
            num_sessions: Number of sessions
            num_events: Number of events
        
        Returns:
            Dictionary with all generated data
        
        Example:
            data = generator.generate_full_dataset()
            print(f"Generated {len(data['users'])} users")
        """
        users = self.generate_users(count=num_users)
        user_ids = [u["id"] for u in users]
        
        sessions = self.generate_sessions(user_ids=user_ids, count=num_sessions)
        session_ids = [s["id"] for s in sessions]
        
        return {
            "users": users,
            "sessions": sessions,
            "memory_session": self.generate_memory_entries(
                session_ids, "session", count=50
            ),
            "memory_working": self.generate_memory_entries(
                session_ids, "working", count=75
            ),
            "memory_longterm": self.generate_memory_entries(
                session_ids, "longterm", count=30
            ),
            "events": self.generate_events(session_ids, count=num_events),
            "work_orders": self.generate_work_orders(session_ids, count=30),
            "knowledge": self.generate_knowledge_entries(count=25),
            "projects": self.generate_projects(user_ids, count=15)
        }
    
    def _random_datetime(self, days_ago: int = 30) -> datetime:
        """Generate random datetime within specified days ago."""
        days_offset = random.randint(0, days_ago)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        
        return datetime.utcnow() - timedelta(
            days=days_offset,
            hours=hours_offset,
            minutes=minutes_offset
        )
    
    def _generate_memory_value(self) -> Dict[str, Any]:
        """Generate realistic memory value data."""
        value_types = [
            lambda: {"text": self.faker.sentence()},
            lambda: {"number": random.randint(1, 1000)},
            lambda: {"list": [self.faker.word() for _ in range(random.randint(2, 6))]},
            lambda: {
                "structured": {
                    "field1": self.faker.word(),
                    "field2": random.randint(1, 100),
                    "field3": self.faker.sentence()
                }
            }
        ]
        
        return random.choice(value_types)()
