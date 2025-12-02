"""
Seed script for Projects and Tasks test data.

Usage:
    python seed_projects_data.py
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.services.client_manager import get_supabase_client
from datetime import datetime, timedelta

# Test constants
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


async def seed_projects():
    """Seed Projects with sample data."""
    print("🔄 Seeding Projects...")
    
    client = get_supabase_client()
    
    # Sample projects
    projects = [
        {
            "title": "Archon Production Beta",
            "description": "Complete Week 1 tasks to reach production beta status",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "user_id": TEST_USER_ID
        },
        {
            "title": "Memory System Enhancement",
            "description": "Improve memory consolidation and retrieval performance",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "user_id": TEST_USER_ID
        },
        {
            "title": "Knowledge Base Expansion",
            "description": "Add more documentation sources and improve search relevance",
            "status": "planning",
            "created_at": datetime.utcnow().isoformat(),
            "user_id": TEST_USER_ID
        },
    ]
    
    created_projects = []
    for project in projects:
        try:
            result = client.table("archon_projects").insert(project).execute()
            if result.data:
                created_projects.append(result.data[0])
                print(f"  ✅ Created project: {project['title']}")
        except Exception as e:
            print(f"  ⚠️  Project might already exist: {project['title']}")
    
    # Sample tasks for first project (Archon Production Beta)
    if created_projects:
        project_id = created_projects[0]["id"]
        tasks = [
            {
                "project_id": project_id,
                "title": "Day 1: Error Handling Foundation",
                "description": "Add custom exceptions, circuit breakers, retry logic",
                "status": "completed",
                "priority": "high",
                "assignee": "AI Assistant",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "project_id": project_id,
                "title": "Day 2: Testing Infrastructure",
                "description": "Set up pytest, create mock clients, write unit tests",
                "status": "completed",
                "priority": "high",
                "assignee": "AI Assistant",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "project_id": project_id,
                "title": "Day 3: Critical Path Testing",
                "description": "Write 35+ integration tests for all APIs",
                "status": "completed",
                "priority": "high",
                "assignee": "AI Assistant",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "project_id": project_id,
                "title": "Day 4: Data Seeding",
                "description": "Create seed scripts for all data layers",
                "status": "in_progress",
                "priority": "medium",
                "assignee": "AI Assistant",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "project_id": project_id,
                "title": "Day 5: Logging & Review",
                "description": "Implement structured logging and review Week 1",
                "status": "todo",
                "priority": "medium",
                "assignee": "AI Assistant",
                "created_at": datetime.utcnow().isoformat()
            },
        ]
        
        # Add tasks for Memory System Enhancement project
        if len(created_projects) > 1:
            memory_project_id = created_projects[1]["id"]
            tasks.extend([
                {
                    "project_id": memory_project_id,
                    "title": "Implement memory consolidation worker",
                    "description": "Create background worker to consolidate memories",
                    "status": "todo",
                    "priority": "high",
                    "assignee": "Backend Team",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "project_id": memory_project_id,
                    "title": "Optimize vector similarity search",
                    "description": "Improve pgvector query performance",
                    "status": "todo",
                    "priority": "medium",
                    "assignee": "Backend Team",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "project_id": memory_project_id,
                    "title": "Add memory pruning logic",
                    "description": "Automatically remove low-importance memories",
                    "status": "planning",
                    "priority": "low",
                    "assignee": "Backend Team",
                    "created_at": datetime.utcnow().isoformat()
                },
            ])
        
        # Add tasks for Knowledge Base project
        if len(created_projects) > 2:
            kb_project_id = created_projects[2]["id"]
            tasks.extend([
                {
                    "project_id": kb_project_id,
                    "title": "Add GitHub documentation crawler",
                    "description": "Crawl and index GitHub repos documentation",
                    "status": "planning",
                    "priority": "medium",
                    "assignee": "Full Stack Team",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "project_id": kb_project_id,
                    "title": "Improve relevance ranking",
                    "description": "Implement BM25 + vector hybrid search",
                    "status": "planning",
                    "priority": "high",
                    "assignee": "Backend Team",
                    "created_at": datetime.utcnow().isoformat()
                },
            ])
        
        for task in tasks:
            try:
                client.table("archon_tasks").insert(task).execute()
                print(f"  ✅ Created task: {task['title']}")
            except Exception as e:
                print(f"  ⚠️  Task might already exist: {task['title']}")
    
    print(f"  ✅ Projects seeded with {len(created_projects)} projects and {len(tasks)} tasks")


async def main():
    """Main seeding function."""
    print("\n" + "="*50)
    print("  ARCHON PROJECTS SEEDING")
    print("="*50 + "\n")
    
    try:
        await seed_projects()
        
        print("\n" + "="*50)
        print("  ✅ PROJECTS SEEDED!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding projects: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
