"""
Integration test for WorkingMemory and LongTermMemory.
This script verifies the Postgres-based memory services work correctly.

Run with: cd python && uv run --with supabase ../verify_postgres_memory.py
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add python directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

from src.memory.working_memory import WorkingMemory
from src.memory.long_term_memory import LongTermMemory

# Generate a test user ID (UUID)
import uuid
TEST_USER_ID = str(uuid.uuid4())

async def test_working_memory():
    print("\n=== Testing Working Memory ===")
    wm = WorkingMemory()
    
    # 1. Create a working memory entry
    entry = await wm.create(
        user_id=TEST_USER_ID,
        memory_type="conversation",
        content={"summary": "Test conversation about memory system"},
        metadata={"test": True},
        ttl_days=7
    )
    print(f"✅ Created working memory: {entry.id}")
    
    # 2. Retrieve recent memories
    recent = await wm.get_recent(TEST_USER_ID, limit=5)
    print(f"✅ Retrieved {len(recent)} recent memories")
    assert len(recent) >= 1
    
    # 3. Cleanup (should find nothing to delete since TTL is 7 days)
    deleted = await wm.cleanup_expired()
    print(f"✅ Cleanup check: {deleted} expired entries")
    
    return entry.id

async def test_long_term_memory():
    print("\n=== Testing Long-Term Memory ===")
    ltm = LongTermMemory()
    
    # 1. Create a long-term memory entry
    entry = await ltm.create(
        user_id=TEST_USER_ID,
        memory_type="fact",
        content={"fact": "User is building Archon, an AI command center"},
        importance_score=0.9
    )
    print(f"✅ Created long-term memory: {entry.id}")
    
    # 2. Retrieve by type
    facts = await ltm.get_by_type(TEST_USER_ID, "fact", limit=5)
    print(f"✅ Retrieved {len(facts)} facts")
    assert len(facts) >= 1
    
    # 3. Get important memories
    important = await ltm.get_important(TEST_USER_ID, min_importance=0.7, limit=5)
    print(f"✅ Retrieved {len(important)} important memories")
    
    # 4. Update access (simulate retrieval)
    updated = await ltm.update_access(entry.id)
    print(f"✅ Updated access count: {updated.access_count}")
    assert updated.access_count == 1
    
    return entry.id

async def main():
    print("Starting Postgres Memory Verification...")
    print("Ensure migration V5_memory_system.sql has been run in Supabase!")
    
    try:
        wm_id = await test_working_memory()
        ltm_id = await test_long_term_memory()
        
        print("\n✅ SUCCESS: All Postgres Memory tests passed!")
        print(f"   - Working Memory ID: {wm_id}")
        print(f"   - Long-Term Memory ID: {ltm_id}")
        
    except Exception as e:
        print(f"\n❌ FAILURE: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())
