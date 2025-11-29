"""
Integration test for ContextAssembler.
Verifies that all 3 memory layers are correctly assembled into unified context.

Run with: cd python && uv run --with supabase --with redis --with python-dotenv ../verify_context_assembler.py
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add python directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

from src.memory import (
    SessionMemory, WorkingMemory, LongTermMemory,
    ContextAssembler, Message
)

# Generate test IDs
TEST_USER_ID = str(uuid.uuid4())
TEST_SESSION_ID = str(uuid.uuid4())

async def setup_test_data():
    """Create test data in all 3 memory layers."""
    print("\n=== Setting Up Test Data ===")
    
    # 1. Create Session Memory
    sm = SessionMemory()
    await sm.connect()
    session = await sm.create_session(TEST_USER_ID, TEST_SESSION_ID)
    await sm.add_message(TEST_SESSION_ID, Message(
        role="user",
        content="I'm building Archon, can you help me plan the memory system?"
    ))
    await sm.add_message(TEST_SESSION_ID, Message(
        role="assistant",
        content="I'll help you design a 4-layer memory architecture."
    ))
    print(f"✅ Created session with {len(session.messages)} messages")
    
    # 2. Create Working Memory
    wm = WorkingMemory()
    await wm.create(
        user_id=TEST_USER_ID,
        session_id=TEST_SESSION_ID,
        memory_type="conversation",
        content={"summary": "Discussed memory architecture design"},
        ttl_days=7
    )
    await wm.create(
        user_id=TEST_USER_ID,
        memory_type="action",
        content={"action": "implemented_session_memory", "status": "complete"},
        ttl_days=30
    )
    print(f"✅ Created 2 working memories")
    
    # 3. Create Long-Term Memory
    ltm = LongTermMemory()
    await ltm.create(
        user_id=TEST_USER_ID,
        memory_type="fact",
        content={"fact": "User is building Archon with Python/React"},
        importance_score=0.9
    )
    await ltm.create(
        user_id=TEST_USER_ID,
        memory_type="preference",
        content={"preference": "User prefers detailed technical explanations"},
        importance_score=0.8
    )
    print(f"✅ Created 2 long-term memories")
    
    await sm.close()

async def test_context_assembler():
    """Test ContextAssembler with all 3 layers."""
    print("\n=== Testing Context Assembler ===")
    
    assembler = ContextAssembler()
    
    # Assemble context with generous token budget
    context = await assembler.assemble_context(
        user_id=TEST_USER_ID,
        session_id=TEST_SESSION_ID,
        max_tokens=8000
    )
    
    print(f"\n📊 Assembled Context:")
    print(f"  - Session: {'✅ Present' if context.session else '❌ Missing'}")
    print(f"    Messages: {len(context.session.messages) if context.session else 0}")
    print(f"  - Recent Memories: {len(context.recent_memories)}")
    print(f"  - Facts: {len(context.facts)}")
    print(f"  - Total Tokens: {context.total_tokens}")
    
    # Assertions
    assert context.session is not None, "Session should be present"
    assert len(context.session.messages) == 2, "Should have 2 messages"
    assert len(context.recent_memories) > 0, "Should have recent memories"
    assert len(context.facts) > 0, "Should have facts"
    assert context.total_tokens > 0, "Token count should be positive"
    
    print("\n✅ All assertions passed!")
    
    # Test with limited token budget
    print("\n=== Testing Token Budget Limit ===")
    limited_context = await assembler.assemble_context(
        user_id=TEST_USER_ID,
        session_id=TEST_SESSION_ID,
        max_tokens=500  # Very small budget
    )
    
    print(f"  - Total Tokens (limited): {limited_context.total_tokens}")
    assert limited_context.total_tokens <= 500, "Should respect token limit"
    print("✅ Token budget respected!")

async def main():
    print("Starting Context Assembler Verification...")
    print("Ensure Redis is running and Supabase migration V5 is applied!")
    
    try:
        await setup_test_data()
        await test_context_assembler()
        
        print("\n🎉 SUCCESS: Context Assembler working perfectly!")
        print(f"   All 3 memory layers unified into single context")
        
    except Exception as e:
        print(f"\n❌ FAILURE: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())
