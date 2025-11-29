"""
Mock Data Generator for Archon Testing

Generates realistic test data for all testing scenarios.
Enables comprehensive testing without needing live services.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from faker import Faker
import uuid
import random

fake = Faker()
Faker.seed(42)  # Reproducible data


class MockDataGenerator:
    """Generate realistic test data for Archon system testing."""
    
    def __init__(self):
        self.fake = fake
        
    # ============================================================================
    # USER DATA
    # ============================================================================
    
    def generate_user(self, user_id: str = None) -> Dict[str, Any]:
        """Generate a realistic user."""
        return {
            "user_id": user_id or f"user_{uuid.uuid4().hex[:8]}",
            "name": self.fake.name(),
            "email": self.fake.email(),
            "created_at": self.fake.date_time_between(start_date="-1y").isoformat()
        }
    
    def generate_users(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate multiple users."""
        return [self.generate_user() for _ in range(count)]
    
    # ============================================================================
    # CONVERSATION DATA
    # ============================================================================
    
    def generate_message(self, role: str, topic: str = None) -> Dict[str, Any]:
        """Generate a single message."""
        if role == "user":
            if topic == "customer_support":
                content = random.choice([
                    "How do I reset my password?",
                    "I'm having trouble logging in",
                    "Can you help me with my account?",
                    "I need to update my billing information",
                    "How do I cancel my subscription?"
                ])
            elif topic == "code_review":
                content = random.choice([
                    "Can you review this Python function?",
                    "Is this the best way to handle errors?",
                    "How can I optimize this query?",
                    "What's wrong with this code?",
                    "Can you suggest improvements?"
                ])
            else:
                content = self.fake.sentence(nb_words=random.randint(5, 20))
        else:  # assistant
            content = self.fake.paragraph(nb_sentences=random.randint(2, 5))
            
        return {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_conversation(
        self,
        turns: int = 10,
        topic: str = None
    ) -> List[Dict[str, Any]]:
        """Generate a realistic conversation."""
        messages = []
        for i in range(turns):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append(self.generate_message(role, topic))
        return messages
    
    # ============================================================================
    # MEMORY DATA
    # ============================================================================
    
    def generate_working_memory(
        self,
        user_id: str,
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """Generate working memory entries."""
        entries = []
        memory_types = ["conversation", "task", "preference", "observation"]
        
        for _ in range(count):
            mem_type = random.choice(memory_types)
            
            if mem_type == "conversation":
                content = {
                    "summary": self.fake.sentence(),
                    "key_points": [self.fake.sentence() for _ in range(3)],
                    "participants": [self.fake.name(), self.fake.name()]
                }
            elif mem_type == "task":
                content = {
                    "title": self.fake.bs(),
                    "status": random.choice(["pending", "in_progress", "completed"]),
                    "priority": random.choice(["low", "medium", "high"])
                }
            elif mem_type == "preference":
                content = {
                    "preference": self.fake.sentence(),
                    "category": random.choice(["ui", "workflow", "communication"])
                }
            else:  # observation
                content = {
                    "observation": self.fake.paragraph(),
                    "context": self.fake.sentence()
                }
            
            entries.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "memory_type": mem_type,
                "content": content,
                "metadata": {
                    "source": random.choice(["chat", "api", "system"]),
                    "confidence": random.uniform(0.5, 1.0)
                },
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "expires_at": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
            })
        
        return entries
    
    def generate_longterm_memory(
        self,
        user_id: str,
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """Generate long-term memory entries (facts)."""
        entries = []
        fact_types = ["fact", "preference", "skill", "goal"]
        
        for _ in range(count):
            fact_type = random.choice(fact_types)
            
            if fact_type == "fact":
                content = {
                    "fact": self.fake.sentence(),
                    "context": self.fake.paragraph()
                }
            elif fact_type == "preference":
                content = {
                    "preference": self.fake.sentence(),
                    "strength": random.choice(["weak", "moderate", "strong"])
                }
            elif fact_type == "skill":
                content = {
                    "skill": self.fake.job(),
                    "proficiency": random.choice(["beginner", "intermediate", "expert"])
                }
            else:  # goal
                content = {
                    "goal": self.fake.bs(),
                    "deadline": self.fake.future_date().isoformat()
                }
            
            entries.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "memory_type": fact_type,
                "content": content,
                "importance": random.uniform(0.5, 1.0),
                "metadata": {
                    "verified": random.choice([True, False]),
                    "source": random.choice(["user_stated", "inferred", "learned"])
                },
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "last_accessed": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "access_count": random.randint(1, 100)
            })
        
        return entries
    
    # ============================================================================
    # PROJECT DATA
    # ============================================================================
    
    def generate_task(self) -> Dict[str, Any]:
        """Generate a project task."""
        return {
            "id": str(uuid.uuid4()),
            "title": self.fake.bs(),
            "description": self.fake.paragraph(),
            "status": random.choice(["todo", "in_progress", "review", "done"]),
            "priority": random.choice(["low", "medium", "high", "urgent"]),
            "assigned_to": self.fake.name(),
            "created_at": self.fake.date_time_between(start_date="-30d").isoformat(),
            "due_date": self.fake.future_date(end_date="+30d").isoformat()
        }
    
    def generate_project(self) -> Dict[str, Any]:
        """Generate a complete project."""
        return {
            "id": str(uuid.uuid4()),
            "name": self.fake.catch_phrase(),
            "description": self.fake.paragraph(nb_sentences=5),
            "status": random.choice(["planning", "active", "on_hold", "completed"]),
            "tasks": [self.generate_task() for _ in range(random.randint(3, 10))],
            "files": [self.fake.file_name() for _ in range(random.randint(5, 15))],
            "team_members": [self.fake.name() for _ in range(random.randint(2, 5))],
            "created_at": self.fake.date_time_between(start_date="-90d").isoformat(),
            "updated_at": self.fake.date_time_between(start_date="-7d").isoformat()
        }
    
    # ============================================================================
    # TEST SCENARIOS
    # ============================================================================
    
    def scenario_customer_support(self) -> Dict[str, Any]:
        """
        Scenario 1: Customer Support Session
        
        A customer service agent handles multiple support queries.
        Tests: Session memory, context switching, knowledge retrieval.
        """
        user = self.generate_user(user_id="support_agent_001")
        
        return {
            "name": "Customer Support",
            "description": "Agent handles 10 customer support conversations",
            "user": user,
            "conversations": [
                self.generate_conversation(turns=6, topic="customer_support")
                for _ in range(10)
            ],
            "working_memory": self.generate_working_memory(user["user_id"], count=15),
            "longterm_memory": self.generate_longterm_memory(user["user_id"], count=30),
            "expected_outcomes": {
                "session_messages": 60,  # 10 conversations * 6 turns
                "working_memories": 15,
                "longterm_facts": 30,
                "context_usage": "high"  # Should use lots of past tickets
            }
        }
    
    def scenario_code_review(self) -> Dict[str, Any]:
        """
        Scenario 2: Code Review Workflow
        
        Developer reviews code with AI assistant.
        Tests: Technical memory, code context, iterative refinement.
        """
        user = self.generate_user(user_id="dev_reviewer_001")
        
        return {
            "name": "Code Review",
            "description": "Developer reviews code with AI assistance",
            "user": user,
            "conversations": [
                self.generate_conversation(turns=8, topic="code_review")
                for _ in range(5)
            ],
            "working_memory": self.generate_working_memory(user["user_id"], count=25),
            "longterm_memory": self.generate_longterm_memory(user["user_id"], count=40),
            "projects": [self.generate_project() for _ in range(3)],
            "expected_outcomes": {
                "session_messages": 40,
                "working_memories": 25,
                "longterm_facts": 40,
                "context_usage": "technical"
            }
        }
    
    def scenario_data_analysis(self) -> Dict[str, Any]:
        """
        Scenario 3: Data Analysis Task
        
        Analyst queries data and generates insights.
        Tests: Structured data handling, fact extraction.
        """
        user = self.generate_user(user_id="analyst_001")
        
        conversation = self.generate_conversation(turns=12, topic=None)
        # Add data-specific messages
        conversation[0]["content"] = "Analyze the sales data for Q4"
        conversation[2]["content"] = "What were the top 5 products?"
        conversation[4]["content"] = "Show me the trend over time"
        
        return {
            "name": "Data Analysis",
            "description": "Analyst queries and analyzes data",
            "user": user,
            "conversations": [conversation],
            "working_memory": self.generate_working_memory(user["user_id"], count=10),
            "longterm_memory": self.generate_longterm_memory(user["user_id"], count=20),
            "expected_outcomes": {
                "session_messages": 12,
                "working_memories": 10,
                "longterm_facts": 20,
                "context_usage": "analytical"
            }
        }
    
    def scenario_content_creation(self) -> Dict[str, Any]:
        """
        Scenario 4: Content Creation Project
        
        Writer creates content with AI assistance.
        Tests: Multi-step workflows, revision tracking.
        """
        user = self.generate_user(user_id="writer_001")
        
        return {
            "name": "Content Creation",
            "description": "Writer creates blog posts with AI",
            "user": user,
            "conversations": [
                self.generate_conversation(turns=20, topic=None)
            ],
            "working_memory": self.generate_working_memory(user["user_id"], count=30),
            "longterm_memory": self.generate_longterm_memory(user["user_id"], count=50),
            "projects": [self.generate_project()],
            "expected_outcomes": {
                "session_messages": 20,
                "working_memories": 30,
                "longterm_facts": 50,
                "context_usage": "creative"
            }
        }
    
    def scenario_multi_agent_collaboration(self) -> Dict[str, Any]:
        """
        Scenario 5: Multi-Agent Collaboration
        
        Multiple agents work together on a complex task.
        Tests: Agent coordination, shared context.
        """
        users = self.generate_users(count=3)
        
        return {
            "name": "Multi-Agent Collaboration",
            "description": "3 agents collaborate on a project",
            "users": users,
            "conversations": [
                self.generate_conversation(turns=15, topic=None)
                for _ in range(3)
            ],
            "working_memory": {
                user["user_id"]: self.generate_working_memory(user["user_id"], count=20)
                for user in users
            },
            "longterm_memory": {
                user["user_id"]: self.generate_longterm_memory(user["user_id"], count=30)
                for user in users
            },
            "projects": [self.generate_project()],
            "expected_outcomes": {
                "total_agents": 3,
                "session_messages": 45,
                "working_memories": 60,
                "longterm_facts": 90,
                "context_usage": "collaborative"
            }
        }
    
    def generate_all_scenarios(self) -> List[Dict[str, Any]]:
        """Generate all 5 test scenarios."""
        return [
            self.scenario_customer_support(),
            self.scenario_code_review(),
            self.scenario_data_analysis(),
            self.scenario_content_creation(),
            self.scenario_multi_agent_collaboration()
        ]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_mock_generator() -> MockDataGenerator:
    """Get a MockDataGenerator instance."""
    return MockDataGenerator()


def generate_scenario(name: str) -> Dict[str, Any]:
    """
    Generate a specific scenario by name.
    
    Args:
        name: One of: customer_support, code_review, data_analysis,
              content_creation, multi_agent
    
    Returns:
        Scenario data dictionary
    """
    gen = MockDataGenerator()
    
    scenarios = {
        "customer_support": gen.scenario_customer_support,
        "code_review": gen.scenario_code_review,
        "data_analysis": gen.scenario_data_analysis,
        "content_creation": gen.scenario_content_creation,
        "multi_agent": gen.scenario_multi_agent_collaboration
    }
    
    if name not in scenarios:
        raise ValueError(f"Unknown scenario: {name}. Choose from: {list(scenarios.keys())}")
    
    return scenarios[name]()


if __name__ == "__main__":
    # Demo: Generate all scenarios
    gen = MockDataGenerator()
    scenarios = gen.generate_all_scenarios()
    
    print("Generated Test Scenarios:\n")
    for scenario in scenarios:
        print(f"📊 {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Expected outcomes: {scenario['expected_outcomes']}")
        print()
