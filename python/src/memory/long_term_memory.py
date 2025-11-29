import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from structlog import get_logger

from src.events import get_event_bus, EventType
from .models import LongTermMemoryEntry

logger = get_logger(__name__)

class LongTermMemory:
    """
    PostgreSQL-based long-term memory implementation.
    Stores permanent knowledge (facts, preferences, skills, relationships).
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        url = supabase_url or os.getenv("SUPABASE_URL")
        key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.client: Client = create_client(url, key)
        self.table_name = "long_term_memory"
        
    async def create(
        self,
        user_id: str,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5
    ) -> LongTermMemoryEntry:
        """Create a new long-term memory entry."""
        data = {
            "user_id": user_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "importance_score": importance_score,
            "access_count": 0
        }
        
        result = self.client.table(self.table_name).insert(data).execute()
        entry = LongTermMemoryEntry(**result.data[0])
        
        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.MEMORY_LONGTERM_CREATED,
                payload={
                    "memory_id": str(entry.id),
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "content": content,
                    "importance_score": importance_score
                },
                user_id=user_id
            )
        except Exception as e:
            logger.error("Failed to publish MEMORY_LONGTERM_CREATED event", error=str(e), user_id=user_id)
            pass
            
        return entry
        
    async def get_by_type(
        self,
        user_id: str,
        memory_type: str,
        limit: int = 10
    ) -> List[LongTermMemoryEntry]:
        """Retrieve long-term memories by type."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .eq("memory_type", memory_type)
            .order("importance_score", desc=True)
            .limit(limit)
            .execute()
        )
        return [LongTermMemoryEntry(**item) for item in result.data]
        
    async def get_important(
        self,
        user_id: str,
        min_importance: float = 0.7,
        limit: int = 10
    ) -> List[LongTermMemoryEntry]:
        """Retrieve high-importance memories."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .gte("importance_score", min_importance)
            .order("importance_score", desc=True)
            .limit(limit)
            .execute()
        )
        return [LongTermMemoryEntry(**item) for item in result.data]
        
    async def update_access(self, memory_id: str) -> LongTermMemoryEntry:
        """Update last_accessed_at and increment access_count."""
        # First get current access count
        current = self.client.table(self.table_name).select("access_count").eq("id", memory_id).execute()
        new_count = (current.data[0]["access_count"] if current.data else 0) + 1
        
        result = (
            self.client.table(self.table_name)
            .update({
                "last_accessed_at": datetime.utcnow().isoformat(),
                "access_count": new_count
            })
            .eq("id", memory_id)
            .execute()
        )
        return LongTermMemoryEntry(**result.data[0])
        
    async def decay_importance(self) -> int:
        """Decay importance of rarely accessed memories."""
        # Call the decay function
        result = self.client.rpc("decay_long_term_importance").execute()
        return result.data if result.data else 0
