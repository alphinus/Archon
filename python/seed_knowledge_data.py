"""
Seed script for Knowledge Base test data.
Creates sample sources and crawled pages.

Usage:
    python seed_knowledge_data.py
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.services.client_manager import get_supabase_client
from datetime import datetime

# Test constants
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


async def seed_knowledge_base():
    """Seed Knowledge Base with sample documents."""
    print("🔄 Seeding Knowledge Base...")
    
    client = get_supabase_client()
    
    # Sample sources
    sources = [
        {
            "source_url": "https://fastapi.tiangolo.com",
            "source_display_name": "FastAPI Documentation",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "source_url": "https://react.dev",
            "source_display_name": "React Documentation",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "source_url": "https://www.postgresql.org/docs",
            "source_display_name": "PostgreSQL Documentation",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "source_url": "https://redis.io/documentation",
            "source_display_name": "Redis Documentation",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "source_url": "https://supabase.com/docs",
            "source_display_name": "Supabase Documentation",
            "created_at": datetime.utcnow().isoformat()
        },
    ]
    
    created_sources = []
    for source in sources:
        try:
            result = client.table("archon_sources").insert(source).execute()
            if result.data:
                created_sources.append(result.data[0])
                print(f"  ✅ Created source: {source['source_display_name']}")
        except Exception as e:
            print(f"  ⚠️  Source might already exist: {source['source_display_name']}")
    
    # Sample pages for first source (FastAPI)
    if created_sources:
        fastapi_source_id = created_sources[0]["id"]
        pages = [
            {
                "source_id": fastapi_source_id,
                "url": "https://fastapi.tiangolo.com/tutorial/",
                "title": "Tutorial - User Guide - FastAPI",
                "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
                "markdown": "# FastAPI Tutorial\n\nLearn how to build APIs with FastAPI...",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "source_id": fastapi_source_id,
                "url": "https://fastapi.tiangolo.com/tutorial/first-steps/",
                "title": "First Steps - FastAPI",
                "content": "Create your first FastAPI application. Install fastapi and uvicorn...",
                "markdown": "# First Steps\n\nInstall FastAPI: pip install fastapi...",
                "created_at": datetime.utcnow().isoformat()
            },
        ]
        
        for page in pages:
            try:
                client.table("archon_pages").insert(page).execute()
                print(f"  ✅ Added page: {page['title']}")
            except Exception as e:
                print(f"  ⚠️  Page might already exist: {page['title']}")
    
    print(f"  ✅ Knowledge Base seeded with {len(sources)} sources")


async def main():
    """Main seeding function."""
    print("\n" + "="*50)
    print("  ARCHON KNOWLEDGE BASE SEEDING")
    print("="*50 + "\n")
    
    try:
        await seed_knowledge_base()
        
        print("\n" + "="*50)
        print("  ✅ KNOWLEDGE BASE SEEDED!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding knowledge base: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
