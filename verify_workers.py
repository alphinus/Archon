"""
Verification script for Background Workers.
Tests that workers run and publish events.

Run with: cd python && uv run --with supabase --with redis --with python-dotenv --with asyncpg ../verify_workers.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add python directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

from src.events import get_event_bus, EventType
from src.workers import MemoryConsolidator, CleanupWorker

received_events = []

async def event_handler(payload):
    """Test event handler."""
    print(f"📥 Received worker event: {payload}")
    received_events.append(payload)

async def main():
    print("=== Verifying Background Workers ===\n")
    
    bus = get_event_bus()
    
    try:
        # 1. Start listening for events
        print("1. Starting Event Bus listener...")
        listen_task = asyncio.create_task(bus.start_listening())
        await asyncio.sleep(1)
        
        # 2. Subscribe to cleanup events
        print(f"2. Subscribing to {EventType.SYSTEM_CLEANUP_TRIGGERED}...")
        bus.subscribe(EventType.SYSTEM_CLEANUP_TRIGGERED, event_handler)
        
        # 3. Run MemoryConsolidator once
        print("3. Running MemoryConsolidator...")
        consolidator = MemoryConsolidator(interval_seconds=1)
        await consolidator.run() # Run directly instead of start() loop
        
        # 4. Run CleanupWorker once
        print("4. Running CleanupWorker...")
        cleanup = CleanupWorker(interval_seconds=1)
        await cleanup.run() # Run directly
        
        # 5. Wait for events
        print("5. Waiting for events...")
        await asyncio.sleep(2)
        
        # 6. Verify
        print(f"\nReceived {len(received_events)} events")
        
        consolidator_events = [e for e in received_events if e.get("worker") == "MemoryConsolidator"]
        cleanup_events = [e for e in received_events if e.get("worker") == "CleanupWorker"]
        
        if len(consolidator_events) > 0 and len(cleanup_events) > 0:
            print("✅ SUCCESS: Both workers ran and published events!")
        else:
            print("❌ FAILURE: Missing events.")
            if not consolidator_events: print("   - MemoryConsolidator event missing")
            if not cleanup_events: print("   - CleanupWorker event missing")
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
        if 'listen_task' in locals() and not listen_task.done():
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
