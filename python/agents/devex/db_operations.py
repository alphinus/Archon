"""
Database Operations for CLI

Handles database seeding, migration, backup, and reset operations.
"""

from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_db_operation(
    operation: str,
    environment: str = "dev"
) -> Dict[str, Any]:
    """
    Run database operation.
    
    Args:
        operation: Operation type (seed, migrate, reset, backup)
        environment: Environment name
    
    Returns:
        Operation result
    """
    operations = {
        "seed": seed_database,
        "migrate": migrate_database,
        "reset": reset_database,
        "backup": backup_database
    }
    
    if operation not in operations:
        return {
            "status": "error",
            "error": f"Unknown operation: {operation}"
        }
    
    try:
        result = await operations[operation](environment)
        return result
    except Exception as e:
        logger.error(f"Database operation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def seed_database(environment: str) -> Dict[str, Any]:
    """Seed database with test data."""
    logger.info(f"Seeding database for {environment}...")
    
    # Call Data Agent's seed skill
    from agents.devex.agent import get_event_bus
    
    event_bus = get_event_bus()
    
    # Publish seed request to Data Agent
    correlation_id = "seed_" + environment
    
    await event_bus.publish(
        "agent.data.request",
        {
            "correlation_id": correlation_id,
            "skill": "seed_database",
            "params": {
                "environment": environment,
                "clear_existing": True
            }
        }
    )
    
    # Wait for response (simplified - in production use proper response handling)
    await asyncio.sleep(2)
    
    return {
        "status": "success",
        "details": f"Database seeded for {environment}"
    }


async def migrate_database(environment: str) -> Dict[str, Any]:
    """Run database migrations."""
    logger.info(f"Running migrations for {environment}...")
    
    import subprocess
    
    # Run Alembic migrations
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return {
            "status": "success",
            "details": "Migrations completed"
        }
    else:
        return {
            "status": "error",
            "error": result.stderr
        }


async def reset_database(environment: str) -> Dict[str, Any]:
    """Reset database (DESTRUCTIVE)."""
    logger.warning(f"Resetting database for {environment}...")
    
    import asyncpg
    import os
    
    db_url = os.getenv("DATABASE_URL", "postgresql://archon:archon@localhost:5432/archon")
    
    conn = await asyncpg.connect(db_url)
    
    # Drop all tables
    await conn.execute("DROP SCHEMA public CASCADE")
    await conn.execute("CREATE SCHEMA public")
    
    await conn.close()
    
    # Run migrations to recreate schema
    await migrate_database(environment)
    
    return {
        "status": "success",
        "details": "Database reset complete"
    }


async def backup_database(environment: str) -> Dict[str, Any]:
    """Create database backup."""
    logger.info(f"Backing up database for {environment}...")
    
    import subprocess
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{environment}_{timestamp}.sql"
    
    # Run pg_dump
    result = subprocess.run(
        [
            "pg_dump",
            "-h", "localhost",
            "-U", "archon",
            "-d", "archon",
            "-f", backup_file
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return {
            "status": "success",
            "details": f"Backup created: {backup_file}"
        }
    else:
        return {
            "status": "error",
            "error": result.stderr
        }
