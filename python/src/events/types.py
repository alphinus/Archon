"""
Event types for Archon Real-Time Memory Sync Engine.
"""

from enum import Enum

class EventType(str, Enum):
    """Standard event types in Archon."""
    
    # Memory Events
    MEMORY_SESSION_CREATED = "memory.session.created"
    MEMORY_SESSION_UPDATED = "memory.session.updated"
    MEMORY_WORKING_CREATED = "memory.working.created"
    MEMORY_LONGTERM_CREATED = "memory.longterm.created"
    MEMORY_CONTEXT_ASSEMBLED = "memory.context.assembled"
    
    # Agent Events
    AGENT_REQUEST_STARTED = "agent.request.started"
    AGENT_REQUEST_COMPLETED = "agent.request.completed"
    AGENT_ERROR_OCCURRED = "agent.error.occurred"
    
    # System Events
    SYSTEM_CLEANUP_TRIGGERED = "system.cleanup.triggered"
    SYSTEM_HEALTH_DEGRADED = "system.health.degraded"
