"""
Event Retry Worker.
Automatically retries failed events from the Dead Letter Queue.
"""

from structlog import get_logger
from ..workers.base import BaseWorker
from .dead_letter_queue import DeadLetterQueue
from .bus import get_event_bus

logger = get_logger(__name__)

class EventRetryWorker(BaseWorker):
    """
    Background worker that retries failed events.
    Runs every 5 minutes to process the Dead Letter Queue.
    """
    
    def __init__(self, interval_seconds: int = 300):  # 5 minutes
        super().__init__("EventRetryWorker", interval_seconds)
        self.dlq = DeadLetterQueue()
        self.event_bus = get_event_bus()
        
    async def run(self):
        """Process pending event retries."""
        try:
            # Get events that need retry
            pending = await self.dlq.get_pending_retries(limit=100)
            
            if not pending:
                logger.debug("no_events_to_retry")
                return
            
            logger.info("processing_event_retries", count=len(pending))
            
            for failure in pending:
                await self._retry_event(failure)
                
            # Cleanup old resolved events
            cleaned = await self.dlq.cleanup_old_resolved(days=30)
            if cleaned > 0:
                logger.info("dlq_cleanup_completed", deleted=cleaned)
                
        except Exception as e:
            logger.error("event_retry_worker_failed", error=str(e))
    
    async def _retry_event(self, failure: dict):
        """Retry a single failed event."""
        try:
            # Re-publish the event
            await self.event_bus.publish(
                event_type=failure["event_type"],
                payload=failure["payload"],
                user_id=failure.get("user_id")
            )
            
            # Mark as successful
            await self.dlq.mark_retry_attempt(
                failure_id=failure["id"],
                success=True
            )
            
            logger.info(
                "event_retry_succeeded",
                event_id=failure["event_id"],
                event_type=failure["event_type"]
            )
            
        except Exception as e:
            # Mark as failed with error
            await self.dlq.mark_retry_attempt(
                failure_id=failure["id"],
                success=False,
                error=str(e)
            )
            
            logger.warning(
                "event_retry_failed",
                event_id=failure["event_id"],
                event_type=failure["event_type"],
                error=str(e)
            )
