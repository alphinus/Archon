import json
import os
from datetime import datetime
from typing import Optional, List
import redis.asyncio as redis
from structlog import get_logger

from src.events import get_event_bus, EventType

from .models import Session, Message, SessionContext

logger = get_logger(__name__)

class SessionMemory:
    """
    Redis-based session memory implementation.
    Stores conversation history and context with a TTL.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[redis.Redis] = None
        self.ttl_seconds = 3600  # 1 hour default TTL
        
    async def connect(self):
        """Establish connection to Redis."""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            
    def _get_key(self, session_id: str) -> str:
        return f"session:{session_id}"
        
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> Session:
        """Create a new session or return existing one if session_id provided."""
        await self.connect()
        
        if session_id:
            existing = await self.get_session(session_id)
            if existing:
                return existing
                
        # Create new session
        session = Session(
            session_id=session_id, # If None, Pydantic will generate one
            user_id=user_id,
            messages=[],
            context=SessionContext()
        )
        
        await self.redis.setex(
            self._get_key(session.session_id),
            self.ttl_seconds,
            session.model_dump_json()
        )
        
        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.MEMORY_SESSION_CREATED,
                payload={
                    "session_id": session.session_id,
                    "user_id": user_id
                },
                user_id=user_id
            )
        except Exception as e:
            logger.error("Failed to publish MEMORY_SESSION_CREATED event", error=str(e), session_id=session.session_id, user_id=user_id)
            # Don't fail the operation if event publishing fails
            pass
            
        return session
        
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        await self.connect()
        
        data = await self.redis.get(self._get_key(session_id))
        if not data:
            return None
            
        # Update TTL on access
        await self.redis.expire(self._get_key(session_id), self.ttl_seconds)
        
        return Session.model_validate_json(data)
        
    async def add_message(self, session_id: str, message: Message) -> Optional[Session]:
        """Add a message to the session."""
        await self.connect()
        
        session = await self.get_session(session_id)
        if not session:
            return None
            
        session.messages.append(message)
        session.last_accessed_at = datetime.utcnow()
        
        await self._save_session(session)

        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.MEMORY_MESSAGE_ADDED,
                payload={
                    "session_id": session_id,
                    "message": message.model_dump()
                },
                user_id=session.user_id
            )
        except Exception as e:
            logger.error("Failed to publish MEMORY_MESSAGE_ADDED event", error=str(e), session_id=session_id, user_id=session.user_id)
            pass

        return session
        
    async def update_context(self, session_id: str, context_updates: dict) -> Optional[Session]:
        """Update session context."""
        await self.connect()
        
        session = await self.get_session(session_id)
        if not session:
            return None
            
        # Update context fields
        current_context = session.context.model_dump()
        current_context.update(context_updates)
        session.context = SessionContext(**current_context)
        session.last_accessed_at = datetime.utcnow()
        
        await self._save_session(session)

        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.MEMORY_CONTEXT_UPDATED,
                payload={
                    "session_id": session_id,
                    "context_updates": context_updates
                },
                user_id=session.user_id
            )
        except Exception as e:
            logger.error("Failed to publish MEMORY_CONTEXT_UPDATED event", error=str(e), session_id=session_id, user_id=session.user_id)
            pass

        return session
        
    async def delete_session(self, session_id: str):
        """Delete a session."""
        await self.connect()
        
        # Retrieve session before deleting to get user_id for event
        session = await self.get_session(session_id)
        
        await self.redis.delete(self._get_key(session_id))

        # Publish event
        if session:
            try:
                event_bus = get_event_bus()
                await event_bus.publish(
                    EventType.MEMORY_SESSION_DELETED,
                    payload={
                        "session_id": session_id
                    },
                    user_id=session.user_id
                )
            except Exception as e:
                logger.error("Failed to publish MEMORY_SESSION_DELETED event", error=str(e), session_id=session_id, user_id=session.user_id)
                pass
        else:
            logger.warning("Attempted to delete non-existent session, no event published.", session_id=session_id)
        
    async def _save_session(self, session: Session):
        """Save session to Redis with TTL."""
        await self.connect()
        await self.redis.set(
            self._get_key(session.session_id),
            session.model_dump_json(),
            ex=self.ttl_seconds
        )
