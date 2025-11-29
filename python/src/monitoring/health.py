"""
Deep Health Check System.
Provides comprehensive component-level health monitoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from structlog import get_logger

from src.memory import SessionMemory, WorkingMemory, LongTermMemory
from src.events import get_event_bus
from src.workers.supervisor import WorkerSupervisor

logger = get_logger(__name__)

class HealthChecker:
    """
    Comprehensive health monitoring for all system components.
    """
    
    def __init__(self):
        self.session_memory = SessionMemory()
        self.working_memory = WorkingMemory()
        self.longterm_memory = LongTermMemory()
        self.event_bus = get_event_bus()
        
    async def check_all(self) -> Dict[str, Any]:
        """
        Run deep health check on all components.
        
        Returns comprehensive health status including:
        - Overall system status (healthy/degraded/unhealthy)
        - Component-level health
        - Latencies
        - Error counts
        """
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check all components in parallel
        redis_health, postgres_health, event_health = await asyncio.gather(
            self._check_redis(),
            self._check_postgres(),
            self._check_event_bus(),
            return_exceptions=True
        )
        
        results["components"]["redis"] = redis_health if not isinstance(redis_health, Exception) else {
            "status": "unhealthy",
            "error": str(redis_health)
        }
        
        results["components"]["postgres"] = postgres_health if not isinstance(postgres_health, Exception) else {
            "status": "unhealthy",
            "error": str(postgres_health)
        }
        
        results["components"]["event_bus"] = event_health if not isinstance(event_health, Exception) else {
            "status": "unhealthy",
            "error": str(event_health)
        }
        
        # Determine overall status
        unhealthy_count = sum(
            1 for c in results["components"].values()
            if c.get("status") == "unhealthy"
        )
        
        if unhealthy_count > 0:
            results["status"] = "unhealthy"
        elif any(c.get("status") == "degraded" for c in results["components"].values()):
            results["status"] = "degraded"
            
        return results
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and latency."""
        start = datetime.now()
        
        try:
            # Test Redis connection
            test_key = f"health_check_{start.timestamp()}"
            await self.session_memory.redis_client.set(test_key, "ping", ex=5)
            value = await self.session_memory.redis_client.get(test_key)
            
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            status = "healthy"
            if latency_ms > 100:
                status = "degraded"
            
            return {
                "status": status,
                "latency_ms": round(latency_ms, 2),
                "connected": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }
    
    async def _check_postgres(self) -> Dict[str, Any]:
        """Check Postgres connectivity and latency."""
        start = datetime.now()
        
        try:
            # Test Postgres connection with a simple query
            result = self.working_memory.client.table("archon_working_memory")\
                .select("id")\
                .limit(1)\
                .execute()
            
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            status = "healthy"
            if latency_ms > 200:
                status = "degraded"
            
            return {
                "status": status,
                "latency_ms": round(latency_ms, 2),
                "connected": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }
    
    async def _check_event_bus(self) -> Dict[str, Any]:
        """Check Event Bus connectivity."""
        try:
            connected = self.event_bus.pool is not None
            
            # Check circuit breaker status
            from src.memory.resilient_memory import redis_breaker, postgres_breaker
            
            circuit_status = {
                "redis": redis_breaker.current_state,
                "postgres": postgres_breaker.current_state
            }
            
            # Determine status
            if any(state == "open" for state in circuit_status.values()):
                status = "degraded"
            elif connected:
                status = "healthy"
            else:
                status = "unhealthy"
            
            return {
                "status": status,
                "connected": connected,
                "circuit_breakers": circuit_status
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global instance
_health_checker: Optional[HealthChecker] = None

def get_health_checker() -> HealthChecker:
    """Get or create global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
