"""
Standard Event Handlers.
"""

from typing import Dict, Any
from structlog import get_logger
from ..models import Event

logger = get_logger(__name__)

async def logging_handler(payload: Dict[str, Any]):
    """
    Simple handler that logs all events.
    Useful for debugging and audit trails.
    """
    # In a real app, this might write to an audit log table
    # For now, we just rely on structlog which is already configured
    pass

async def notification_handler(payload: Dict[str, Any]):
    """
    Handler that simulates sending notifications to the UI.
    """
    # In a real app, this would push to a WebSocket or Notification Service
    # For the demo, we'll just log a special message
    event_type = payload.get("event_type", "unknown")
    
    if "memory" in event_type:
        logger.info("ui_notification_sent", message=f"New memory created: {payload.get('memory_type')}")
    elif "agent" in event_type:
        logger.info("ui_notification_sent", message=f"Agent activity: {payload.get('status')}")
