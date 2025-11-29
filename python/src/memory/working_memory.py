import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from structlog import get_logger

from src.events import get_event_bus, EventType
from .models import WorkingMemoryEntry

logger = get_logger(__name__)

class WorkingMemory:
    """
    PostgreSQL-based working memory implementation.
    Stores recent context (conversations, actions, decisions) with 7-30 day TTL.
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        url = supabase_url or os.getenv("SUPABASE_URL")
        key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.client: Client = create_client(url, key)
        self.table_name = "working_memory"
        
    async def create(
        self,
        user_id: str,
        memory_type: str,
        content: Dict[str, Any],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_days: int = 7
    ) -> WorkingMemoryEntry:
        """Create a new working memory entry."""
        expires_at = datetime.utcnow() + timedelta(days=ttl_days)
        
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "expires_at": expires_at.isoformat(),
            "relevance_score": 1.0
        }
        
        result = self.client.table(self.table_name).insert(data).execute()
        entry = WorkingMemoryEntry(**result.data[0])
        
        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.MEMORY_WORKING_CREATED,
                payload={
                    "memory_id": str(entry.id),
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "content": content
                },
                user_id=user_id
            )
        except Exception as e:
            logger.error("Failed to publish MEMORY_WORKING_CREATED event", error=str(e), user_id=user_id)
            pass
            
        return entry
        
    async def get_recent(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[WorkingMemoryEntry]:
        """Retrieve recent working memories for a user."""
        query = self.client.table(self.table_name).select("*").eq("user_id", user_id)
        
        if memory_type:
            query = query.eq("memory_type", memory_type)
            
        result = query.order("created_at", desc=True).limit(limit).execute()
        return [WorkingMemoryEntry(**item) for item in result.data]
        
    async def get_by_session(self, session_id: str) -> List[WorkingMemoryEntry]:
        """Retrieve all working memories for a specific session."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [WorkingMemoryEntry(**item) for item in result.data]
        
    async def cleanup_expired(self) -> int:
        """Remove expired or low-relevance working memories."""
        # Call the cleanup function
        result = self.client.rpc("cleanup_expired_working_memory").execute()
        return result.data if result.data else 0
