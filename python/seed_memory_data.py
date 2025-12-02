#!/usr/bin/env python3
"""
Seed test data for Memory Inspector.
Creates sample data for session, working, and long-term memory layers.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import List

# Test UUIDs for consistency
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID v4
TEST_SESSION_ID = "test_session_001"

async def seed_session_memory():
    """Seed Redis with sample session messages."""
    from src.memory import SessionMemory
    from src.memory.models import Message
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    session_memory = SessionMemory(redis_url=redis_url)
    
    print(f"Creating session: {TEST_SESSION_ID} for user: {TEST_USER_ID}")
    
    # First create the session
    await session_memory.create_session(
        session_id=TEST_SESSION_ID,
        user_id=TEST_USER_ID
    )
    
    # Create sample conversation messages
    messages = [
        Message(role="user", content="Hello! I'm testing the Memory Inspector."),
        Message(role="assistant", content="Hi! I'm here to help you test the memory system. How can I assist you?"),
        Message(role="user", content="Can you remember what I told you about my project?"),
        Message(role="assistant", content="I'd be happy to help! Could you tell me more about your project?"),
        Message(role="user", content="I'm building Archon, a knowledge management system for AI."),
        Message(role="assistant", content="That sounds fascinating! Archon as a knowledge management system will help AIs retain context across sessions."),
    ]
    
    for msg in messages:
        await session_memory.add_message(
            session_id=TEST_SESSION_ID,
            message=msg
        )
    
    print(f"✅ Added {len(messages)} messages to session memory")

async def seed_working_memory():
    """Seed Supabase with sample working memory entries."""
    from src.memory import WorkingMemory
    from src.server.config.config import get_config
    
    config = get_config()
    working_memory = WorkingMemory(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_service_key
    )
    
    # Sample working memory entries
    entries = [
        {
            "content": "User is testing the Memory Inspector UI",
            "memory_type": "context",
            "importance_score": 0.8,
        },
        {
            "content": "User's name is interested in AI systems",
            "memory_type": "user_info",
            "importance_score": 0.7,
        },
        {
            "content": "Current project: Building Archon knowledge system",
            "memory_type": "task",
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
