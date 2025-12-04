"""
System Status Checker

Checks health and status of all Archon components.
"""

from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def get_system_status(detailed: bool = False) -> Dict[str, Any]:
    """
    Get overall system status.
    
    Args:
        detailed: Include detailed information
    
    Returns:
        Status dictionary with all components
    """
    status = {}
    
    # Check all components concurrently
    tasks = {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "server": check_server(),
        "agents": check_agents(),
    }
    
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True
    )
    
    for (name, _), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            status[name] = {
                "status": "unhealthy",
                "error": str(result)
            }
        else:
            status[name] = result
    
    return status


async def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL health."""
    try:
        import asyncpg
        import os
        
        db_url = os.getenv("DATABASE_URL", "postgresql://archon:archon@localhost:5432/archon")
        
        conn = await asyncio.wait_for(
            asyncpg.connect(db_url),
            timeout=5.0
        )
        
        # Simple health check query
        await conn.fetchval("SELECT 1")
        await conn.close()
        
        return {
            "status": "healthy",
            "details": "Connected successfully"
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "details": "Connection timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "details": str(e)
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis health."""
    try:
        import aioredis
        import os
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        redis = await asyncio.wait_for(
            aioredis.from_url(redis_url),
            timeout=5.0
        )
        
        # Simple ping
        await redis.ping()
        await redis.close()
        
        return {
            "status": "healthy",
            "details": "Ping successful"
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "details": "Connection timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "details": str(e)
        }


async def check_server() -> Dict[str, Any]:
    """Check Archon server health."""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8000/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "details": data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "details": f"HTTP {response.status}"
                    }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "details": "Health check timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "details": str(e)
        }


async def check_agents() -> Dict[str, Any]:
    """Check agent health."""
    # Would check individual agents via event bus
    # For now, return mock status
    
    agents = [
        "testing",
        "devex",
        "ui",
        "documentation",
        "orchestration",
        "infrastructure",
        "data"
    ]
    
    agent_status = {}
    for agent in agents:
        # Mock status - in production, query via event bus
        agent_status[agent] = {
            "running": True,
            "skills": []
        }
    
    return {
        "status": "healthy",
        "details": f"{len(agents)} agents available",
        "agents": agent_status
    }
