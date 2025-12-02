#!/usr/bin/env python3
"""
Seed test data for Memory Inspector.
Creates sample data for session, working, and long-term memory layers.
"""
import asyncio
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Make sure we can import from src
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import SessionMemory, WorkingMemory, LongTermMemory
from src.memory.models import Message

# Test constants
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_SESSION_ID = "test_session_001"


async def seed_session_memory():
    """Seed Session Memory with conversation data."""
    print("🔄 Seeding Session Memory...")
    
    memory = SessionMemory()
    await memory.connect()
    
    # Create session
    session = await memory.create_session(
        user_id=TEST_USER_ID,
        session_id=TEST_SESSION_ID
    )
    print(f"  ✅ Created session: {session.session_id}")
    
    # Add conversation messages
    messages = [
        Message(role="user", content="Hello! Can you help me with my project?"),
        Message(role="assistant", content="Of course! I'd be happy to help. What project are you working on?"),
        Message(role="user", content="I'm building a web application with FastAPI and React."),
        Message(role="assistant", content="Great choice! FastAPI is excellent for APIs and React for frontends. What specific help do you need?"),
        Message(role="user", content="I need to implement authentication and user management."),
        Message(role="assistant", content="I can help with that. Let's start with JWT-based authentication..."),
        Message(role="user", content="Should I use OAuth2 or custom authentication?"),
        Message(role="assistant", content="For most cases, OAuth2 with JWT tokens is recommended. Here's why..."),
    ]
    
    for msg in messages:
        await memory.add_message(TEST_SESSION_ID, msg)
    
    print(f"  ✅ Added {len(messages)} messages to session")
    await memory.close()


async def seed_working_memory():
            "importance_score": 0.9,
        },
        {
            "content": "User prefers technical explanations",
            "memory_type": "preference",
            "importance_score": 0.6,
        },
    ]
    
    print(f"Adding {len(entries)} working memory entries for user: {TEST_USER_ID}")
    
    for entry in entries:
        await working_memory.add(
            user_id=TEST_USER_ID,
            content=entry["content"],
            memory_type=entry["memory_type"],
            importance_score=entry["importance_score"]
        )
    
    print("✅ Added working memory entries")

async def seed_longterm_memory():
    """Seed Supabase with sample long-term memory entries."""
    from src.memory import LongTermMemory
    from src.server.config.config import get_config
    
    config = get_config()
    longterm_memory = LongTermMemory(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_service_key
    )
    
    # Sample long-term memory entries
    entries = [
        {
            "content": "Archon is a Model Context Protocol (MCP) server for AI knowledge management",
            "memory_type": "fact",
            "importance_score": 1.0,
        },
        {
            "content": "User is building AI systems with persistent memory",
            "memory_type": "fact",
            "importance_score": 0.9,
        },
        {
            "content": "Memory systems include: Session (short-term), Working (7-30 days), Long-term (permanent)",
            "memory_type": "fact",
            "importance_score": 0.95,
        },
    ]
    
    print(f"Adding {len(entries)} long-term memory entries for user: {TEST_USER_ID}")
    
    for entry in entries:
        await longterm_memory.add(
            user_id=TEST_USER_ID,
            content=entry["content"],
            memory_type=entry["memory_type"],
            importance_score=entry["importance_score"]
        )
    
    print("✅ Added long-term memory entries")

async def main():
    """Seed all memory layers with test data."""
    print("🌱 Seeding Memory Inspector test data...")
    print(f"📝 Test User ID: {TEST_USER_ID}")
    print(f"📝 Test Session ID: {TEST_SESSION_ID}")
    print()
    
    try:
        await seed_session_memory()
        print()
        await seed_working_memory()
        print()
        await seed_longterm_memory()
        print()
        print("✅ All test data seeded successfully!")
        print()
        print("🧪 Test the Memory Inspector at: http://localhost:3737")
        print(f"   - Use User ID: {TEST_USER_ID}")
        print(f"   - Use Session ID: {TEST_SESSION_ID}")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
