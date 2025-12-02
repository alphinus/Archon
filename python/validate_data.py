"""
Data validation script for Archon.
Validates that all seeded data is present and correct.

Usage:
    python validate_data.py
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import SessionMemory, WorkingMemory, LongTermMemory
from src.server.services.client_manager import get_supabase_client

# Test constants
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_SESSION_ID = "test_session_001"


async def validate_session_memory():
    """Validate Session Memory data."""
    print("🔍 Validating Session Memory...")
    
    memory = SessionMemory()
    await memory.connect()
    
    session = await memory.get_session(TEST_SESSION_ID)
    
    if not session:
        print("  ❌ Session not found!")
        return False
    
    if len(session.messages) == 0:
        print("  ❌ No messages in session!")
        return False
    
    print(f"  ✅ Session found with {len(session.messages)} messages")
    await memory.close()
    return True


async def validate_working_memory():
    """Validate Working Memory data."""
    print("🔍 Validating Working Memory...")
    
    memory = WorkingMemory()
    entries = await memory.get_recent(user_id=TEST_USER_ID, limit=50)
    
    if len(entries) == 0:
        print("  ❌ No working memory entries found!")
        return False
    
    print(f"  ✅ Found {len(entries)} working memory entries")
    return True


async def validate_longterm_memory():
    """Validate Long-Term Memory data."""
    print("🔍 Validating Long-Term Memory...")
    
    memory = LongTermMemory()
    entries = await memory.get_important(user_id=TEST_USER_ID, min_importance=0.5, limit=50)
    
    if len(entries) == 0:
        print("  ❌ No long-term memory entries found!")
        return False
    
    print(f"  ✅ Found {len(entries)} long-term memory entries")
    return True


async def validate_knowledge_base():
    """Validate Knowledge Base data."""
    print("🔍 Validating Knowledge Base...")
    
    client = get_supabase_client()
    
    # Check sources
    sources_result = client.table("archon_sources").select("*").execute()
    if len(sources_result.data) == 0:
        print("  ❌ No knowledge sources found!")
        return False
    
    # Check pages
    pages_result = client.table("archon_pages").select("*").execute()
    if len(pages_result.data) == 0:
        print("  ⚠️  No pages found (might not be seeded yet)")
    
    print(f"  ✅ Found {len(sources_result.data)} sources and {len(pages_result.data)} pages")
    return True


async def validate_projects():
    """Validate Projects data."""
    print("🔍 Validating Projects...")
    
    client = get_supabase_client()
    
    # Check projects
    projects_result = client.table("archon_projects").select("*").execute()
    if len(projects_result.data) == 0:
        print("  ❌ No projects found!")
        return False
    
    # Check tasks
    tasks_result = client.table("archon_tasks").select("*").execute()
    if len(tasks_result.data) == 0:
        print("  ⚠️  No tasks found")
    
    print(f"  ✅ Found {len(projects_result.data)} projects and {len(tasks_result.data)} tasks")
    return True


async def main():
    """Main validation function."""
    print("\n" + "="*50)
    print("  ARCHON DATA VALIDATION")
    print("="*50 + "\n")
    
    results = {
        "Session Memory": False,
        "Working Memory": False,
        "Long-Term Memory": False,
        "Knowledge Base": False,
        "Projects": False
    }
    
    try:
        results["Session Memory"] = await validate_session_memory()
        results["Working Memory"] = await validate_working_memory()
        results["Long-Term Memory"] = await validate_longterm_memory()
        results["Knowledge Base"] = await validate_knowledge_base()
        results["Projects"] = await validate_projects()
        
        print("\n" + "="*50)
        print("  VALIDATION SUMMARY")
        print("="*50 + "\n")
        
        all_passed = True
        for component, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}  {component}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*50)
        if all_passed:
            print("  ✅ ALL VALIDATIONS PASSED!")
        else:
            print("  ⚠️  SOME VALIDATIONS FAILED")
        print("="*50 + "\n")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
