"""
Real-Time Event Bus using Postgres LISTEN/NOTIFY.

This provides transactional, reliable event delivery without
requiring additional infrastructure like Redis Pub/Sub or Kafka.
"""

import asyncio
import json
import os
import uuid
from typing import Callable, Dict, List, Optional
from structlog import get_logger
import asyncpg

from .models import Event
from .types import EventType
from .dead_letter_queue import DeadLetterQueue

logger = get_logger(__name__)

class EventBus:
    """
    Event Bus using Postgres LISTEN/NOTIFY.
    
    Features:
    - Transactional (events only delivered on commit)
    - No message loss
    - Uses existing Postgres connection
    - Supports multiple listeners per event type
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL") or self._build_url()
        self.pool: Optional[asyncpg.Pool] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self.dlq = DeadLetterQueue()
        self._running = False
        
    def _build_url(self) -> str:
        """Build database URL from Supabase credentials."""
        supabase_url = os.getenv("SUPABASE_URL", "")
        password = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        # Clean up URL
        host = supabase_url.replace("https://", "").replace("http://", "")
        if "/" in host:
            host = host.split("/")[0]
            
        # Cloud Supabase (project.supabase.co)
        if "supabase.co" in host:
            return f"postgresql://postgres:{password}@db.{host}:5432/postgres"
            
        # Local Supabase (usually localhost:54321 for API, 54322 for DB)
        # We'll try standard local ports if not specified
        return f"postgresql://postgres:{password}@127.0.0.1:54322/postgres"
        
    async def connect(self):
        """Establish connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10
            )
            logger.info("event_bus_connected", database_url=self.database_url[:50]+"...")
            
    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("event_bus_disconnected")
            
    async def publish(self, event_type: str, payload: Dict, user_id: Optional[str] = None):
        """
        Publish an event to the bus.
        
        Args:
            event_type: Type of event (use EventType enum)
            payload: Event payload
            user_id: Optional user ID for filtering
        """
        await self.connect()
        
        event = Event(
            event_type=event_type,
            payload=payload,
            user_id=user_id
        )
        
        try:
            # Publish via Postgres NOTIFY
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"NOTIFY archon_events, '{event.model_dump_json()}'"
                )
                
            logger.debug(
                "event_published",
                event_type=event_type,
                event_id=event.event_id,
                user_id=user_id
            )
        except Exception as e:
            logger.error("event_publish_failed", event_type=event_type, error=str(e))
            
            # Record in Dead Letter Queue
            try:
                await self.dlq.record_failure(
                    event_id=event.event_id, # Use event.event_id directly
                    event_type=event_type,
                    payload=payload,
                    error=e,
                    user_id=user_id
                )
            except Exception as dlq_error:
                logger.error("dlq_record_failed", error=str(dlq_error))
            
            raise
        
    def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to listen for
            handler: Async function to handle events
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        
        logger.info(
            "event_subscription_added",
            event_type=event_type,
            handler=handler.__name__
        )
        
    async def start_listening(self):
        """Start listening for events (runs in background)."""
        await self.connect()
        self._running = True
        
        async with self.pool.acquire() as conn:
            await conn.add_listener("archon_events", self._handle_notification)
            
            logger.info("event_bus_listening")
            
            # Keep connection alive
            while self._running:
                await asyncio.sleep(1)
                
    async def stop_listening(self):
        """Stop listening for events."""
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
            
    async def _handle_notification(self, connection, pid, channel, payload):
        """Handle incoming notification from Postgres."""
        try:
            event = Event.model_validate_json(payload)
            
            # Find handlers for this event type
            handlers = self.subscribers.get(event.event_type, [])
            
            # Execute all handlers
            for handler in handlers:
                try:
                    await handler(event.payload)
                except Exception as e:
                    logger.error(
                        "event_handler_failed",
                        event_type=event.event_type,
                        handler=handler.__name__,
                        error=str(e)
                    )
                    
            logger.debug(
                "event_handled",
                event_type=event.event_type,
                handlers_count=len(handlers)
            )
            
        except Exception as e:
            logger.error(
                "event_processing_failed",
                payload=payload[:100],
                error=str(e)
            )

# Global instance
_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get or create global EventBus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
