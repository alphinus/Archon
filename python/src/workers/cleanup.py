"""
Cleanup Worker.
Removes expired memories and decays importance.
"""

from structlog import get_logger
from src.memory import WorkingMemory, LongTermMemory
from src.events import get_event_bus, EventType
from .base import BaseWorker

logger = get_logger(__name__)

class CleanupWorker(BaseWorker):
    """
    Runs periodic cleanup tasks:
    1. Delete expired Working Memory entries
    2. Decay importance of Long-Term Memory entries
    """
    
    def __init__(self, interval_seconds: int = 86400):  # Run daily
        super().__init__("CleanupWorker", interval_seconds)
        self.wm = WorkingMemory()
        self.ltm = LongTermMemory()
        
    async def run(self):
        """Execute cleanup logic."""
        
        # 1. Clean expired working memory
        deleted_count = await self.wm.cleanup_expired()
        logger.info("cleanup_working_memory", deleted_count=deleted_count)
        
        # 2. Decay long-term memory importance
        decayed_count = await self.ltm.decay_importance()
        logger.info("decay_long_term_memory", decayed_count=decayed_count)
        
        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish(
            EventType.SYSTEM_CLEANUP_TRIGGERED,
            payload={
                "worker": self.name,
                "deleted_working": deleted_count,
                "decayed_longterm": decayed_count
            }
        )
