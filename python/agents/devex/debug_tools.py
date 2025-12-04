"""
Debug Tools for Archon

Provides debugging utilities for memory inspection, event streaming, and more.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class MemoryInspector:
    """
    Interactive memory inspector.
    
    Allows real-time inspection of Archon's 4-layer memory system.
    """
    
    def __init__(self, memory_system: Any):
        self.memory = memory_system
    
    async def inspect(
        self,
        layer: str = "all",
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Inspect memory layer.
        
        Args:
            layer: Memory layer (session, working, longterm, all)
            session_id: Filter by session
            filters: Additional filters
            limit: Max results
        
        Returns:
            Memory entries
        """
        logger.info(f"Inspecting memory layer: {layer}")
        
        filters = filters or {}
        if session_id:
            filters["session_id"] = session_id
        
        if layer == "all":
            return {
                "session": await self._get_layer("session", filters, limit),
                "working": await self._get_layer("working", filters, limit),
                "longterm": await self._get_layer("longterm", filters, limit)
            }
        else:
            return await self._get_layer(layer, filters, limit)
    
    async def _get_layer(
        self,
        layer: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get entries from specific memory layer."""
        # This would integrate with actual memory system
        # For now, return mock data
        return [
            {
                "id": f"mem_{i}",
                "layer": layer,
                "key": f"key_{i}",
                "value": f"value_{i}",
                "created_at": "2024-01-01T00:00:00Z"
            }
            for i in range(min(limit, 5))
        ]
    
    def search(
        self,
        query: str,
        layer: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Search memory by query.
        
        Args:
            query: Search query
            layer: Layer to search
        
        Returns:
            Matching entries
        """
        logger.info(f"Searching memory for: {query}")
        # Implementation would search actual memory
        return []


class EventStreamViewer:
    """
    Real-time event stream viewer.
    
    Displays Archon events as they happen.
    """
    
    def __init__(self, event_bus: Any):
        self.event_bus = event_bus
        self.running = False
    
    async def stream(
        self,
        filters: Optional[Dict[str, Any]] = None,
        callback: Optional[callable] = None
    ):
        """
        Stream events in real-time.
        
        Args:
            filters: Event filters (type, agent, etc.)
            callback: Callback for each event
        """
        self.running = True
        filters = filters or {}
        
        logger.info("Starting event stream...")
        
        async def event_handler(event: Dict[str, Any]):
            if self._matches_filters(event, filters):
                if callback:
                    callback(event)
                else:
                    logger.info(f"Event: {event}")
        
        # Subscribe to all events
        await self.event_bus.subscribe("agent.*", event_handler)
        
        # Keep streaming until stopped
        while self.running:
            await asyncio.sleep(0.1)
    
    def stop(self):
        """Stop streaming."""
        self.running = False
        logger.info("Event stream stopped")
    
    def _matches_filters(
        self,
        event: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Check if event matches filters."""
        for key, value in filters.items():
            if event.get(key) != value:
                return False
        return True


class PerformanceProfiler:
    """
    Performance profiler for Archon components.
    
    Tracks execution times, memory usage, and bottlenecks.
    """
    
    def __init__(self):
        self.profiles = {}
    
    async def profile(
        self,
        component: str,
        operation: callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Profile an operation.
        
        Args:
            component: Component name
            operation: Async callable to profile
            *args, **kwargs: Arguments for operation
        
        Returns:
            Profiling results
        """
        import time
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure before
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute operation
        try:
            result = await operation(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        # Measure after
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        profile_data = {
            "component": component,
            "duration_ms": (end_time - start_time) * 1000,
            "memory_delta_mb": end_memory - start_memory,
            "success": success,
            "error": error
        }
        
        # Store profile
        if component not in self.profiles:
            self.profiles[component] = []
        self.profiles[component].append(profile_data)
        
        logger.info(f"Profile: {component} - {profile_data['duration_ms']:.2f}ms")
        
        return profile_data
    
    def get_stats(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get profiling statistics.
        
        Args:
            component: Specific component (or all if None)
        
        Returns:
            Statistics
        """
        if component:
            profiles = self.profiles.get(component, [])
            return self._compute_stats(profiles)
        else:
            return {
                comp: self._compute_stats(profiles)
                for comp, profiles in self.profiles.items()
            }
    
    def _compute_stats(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistics from profiles."""
        if not profiles:
            return {}
        
        durations = [p["duration_ms"] for p in profiles]
        
        return {
            "count": len(profiles),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "success_rate": sum(1 for p in profiles if p["success"]) / len(profiles)
        }


# Convenience functions

async def inspect_memory(
    layer: str = "all",
    session_id: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Inspect memory layer.
    
    Convenience function for CLI usage.
    """
    # Would get actual memory system instance
    inspector = MemoryInspector(None)
    return await inspector.inspect(layer, session_id, limit=limit)


async def stream_events(
    filters: Optional[Dict[str, Any]] = None
):
    """
    Stream events to console.
    
    Convenience function for CLI usage.
    """
    # Would get actual event bus instance
    viewer = EventStreamViewer(None)
    await viewer.stream(filters)
