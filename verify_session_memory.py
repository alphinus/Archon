import asyncio
import os
import sys
from datetime import datetime

# Add python directory to path relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

from src.memory.session_memory import SessionMemory
from src.memory.models import Message

async def main():
    print("Starting SessionMemory verification...")
    
    # Use a specific DB for testing
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    memory = SessionMemory(redis_url=redis_url)
    
    try:
        await memory.connect()
        print("Connected to Redis.")
        
        # Clean up
        await memory.redis.flushdb()
        
        # 1. Create Session
        user_id = "verify_user"
        session = await memory.create_session(user_id)
        print(f"Session created: {session.session_id}")
        assert session.user_id == user_id
        
        # 2. Add Message
        msg = Message(role="user", content="Hello Verification")
        updated = await memory.add_message(session.session_id, msg)
        print(f"Message added. Count: {len(updated.messages)}")
        assert len(updated.messages) == 1
        assert updated.messages[0].content == "Hello Verification"
        
        # 3. Retrieve Session
        retrieved = await memory.get_session(session.session_id)
        print("Session retrieved.")
        assert retrieved.session_id == session.session_id
        assert len(retrieved.messages) == 1
        
        # 4. Update Context
        updates = {"active_project_id": "proj_verify"}
        updated_ctx = await memory.update_context(session.session_id, updates)
        print(f"Context updated: {updated_ctx.context.active_project_id}")
        assert updated_ctx.context.active_project_id == "proj_verify"
        
        # 5. Delete Session
        await memory.delete_session(session.session_id)
        deleted = await memory.get_session(session.session_id)
        print("Session deleted.")
        assert deleted is None
        
        print("\nSUCCESS: All SessionMemory verification steps passed!")
        
    except Exception as e:
        print(f"\nFAILURE: {e}")
        raise
    finally:
        await memory.close()

if __name__ == "__main__":
    asyncio.run(main())
