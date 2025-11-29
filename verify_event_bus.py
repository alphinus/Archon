"""
Verification script for Event Bus.
Tests Postgres LISTEN/NOTIFY functionality.

Run with: cd python && uv run --with supabase --with redis --with python-dotenv --with asyncpg ../verify_event_bus.py
"""

import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add python directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

from src.events import get_event_bus, EventType

# Test data
TEST_EVENT_TYPE = "test.event"
TEST_PAYLOAD = {"message": "Hello Event Bus!"}
TEST_USER_ID = str(uuid.uuid4())

received_events = []

async def event_handler(payload):
    """Test event handler."""
    print(f"📥 Received event payload: {payload}")
    received_events.append(payload)

async def main():
    print("=== Verifying Event Bus (Postgres LISTEN/NOTIFY) ===\n")
    
    bus = get_event_bus()
    print(f"DEBUG: Connecting to DB URL: {bus.database_url.replace(os.getenv('SUPABASE_SERVICE_KEY', 'xxx'), '***')}")
    
    try:
        # 1. Start listening
        print("1. Starting Event Bus listener...")
        listen_task = asyncio.create_task(bus.start_listening())
        await asyncio.sleep(1)  # Wait for connection
        
        # 2. Subscribe
        print(f"2. Subscribing to {TEST_EVENT_TYPE}...")
        bus.subscribe(TEST_EVENT_TYPE, event_handler)
        
        # 3. Publish
        print(f"3. Publishing event to {TEST_EVENT_TYPE}...")
        await bus.publish(
            TEST_EVENT_TYPE,
            payload=TEST_PAYLOAD,
            user_id=TEST_USER_ID
        )
        
        # 4. Wait for delivery
        print("4. Waiting for event delivery...")
        await asyncio.sleep(2)
        
        # 5. Verify
        if len(received_events) > 0:
            print("\n✅ SUCCESS: Event received!")
            print(f"   Payload: {received_events[0]}")
            assert received_events[0]["message"] == TEST_PAYLOAD["message"]
        else:
            print("\n❌ FAILURE: No event received within timeout.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        print("\nCleaning up...")
        await bus.stop_listening()
        await bus.disconnect()
        # Cancel listen task if still running
        if 'listen_task' in locals() and not listen_task.done():
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
