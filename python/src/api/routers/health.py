"""
Health Check API Router.
Exposes comprehensive health endpoints.
"""

from fastapi import APIRouter
from structlog import get_logger

from src.monitoring.health import get_health_checker

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

@router.get("/deep")
async def deep_health_check():
    """
    Comprehensive health check.
    Tests all system components and returns detailed status.
    """
    checker = get_health_checker()
    return await checker.check_all()

@router.get("/memory")
async def memory_health():
    """Health check specifically for Memory System."""
    checker = get_health_checker()
    results = await checker.check_all()
    
    return {
        "redis": results["components"].get("redis", {}),
        "postgres": results["components"].get("postgres", {})
    }

@router.get("/events")
async def events_health():
    """Health check for Event System."""
    checker = get_health_checker()
    results = await checker.check_all()
    
    return results["components"].get("event_bus", {})

@router.get("/workers")
async def workers_health():
    """Health check for Background Workers."""
    # This would integrate with WorkerSupervisor
    # For now, return a placeholder
    return {
        "status": "not_implemented",
        "message": "Worker health will be exposed via WorkerSupervisor API"
    }
