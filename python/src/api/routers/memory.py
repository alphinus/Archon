```
"""
Memory API Router.
Exposes read-only endpoints for Session, Working, and Long-Term Memory.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from structlog import get_logger
from datetime import datetime

from src.server.exceptions import DatabaseError, ValidationError, NotFoundError
from src.memory import SessionMemory, WorkingMemory, LongTermMemory
from src.memory.models import SessionMessage, WorkingMemoryEntry, LongTermMemoryEntry

logger = get_logger(__name__)
router = APIRouter(prefix="/api/memory", tags=["memory"])

# Response Models for better API documentation
class SessionHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    message_count: int
    messages: List[SessionMessage]
    has_more: bool
    
class WorkingMemoryResponse(BaseModel):
    entries: List[WorkingMemoryEntry]
    total_count: int
    page: int
    page_size: int
    
class LongTermMemoryResponse(BaseModel):
    entries: List[LongTermMemoryEntry]
    total_count: int
    page: int
    page_size: int

class MemoryStatsResponse(BaseModel):
    user_id: str
    working_memory_count: int
    longterm_memory_count: int
    total_memories: int
    avg_importance: Optional[float] = None


# Initialize memory services with proper configuration
# This is done at module level but services connect lazily
def _get_session_memory() -> SessionMemory:
    """Get or create SessionMemory instance with config."""
    import os
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return SessionMemory(redis_url=redis_url)

def _get_working_memory() -> WorkingMemory:
    """Get or create WorkingMemory instance with config."""
    from src.server.config.config import get_config
    config = get_config()
    return WorkingMemory(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_service_key
    )

def _get_longterm_memory() -> LongTermMemory:
    """Get or create LongTermMemory instance with config."""
    from src.server.config.config import get_config
    config = get_config()
    return LongTermMemory(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_service_key
    )

# Lazy initialization - only create when first accessed
_session_memory_instance: Optional[SessionMemory] = None
_working_memory_instance: Optional[WorkingMemory] = None
_longterm_memory_instance: Optional[LongTermMemory] = None

def _get_session_memory_instance() -> SessionMemory:
    global _session_memory_instance
    if _session_memory_instance is None:
        _session_memory_instance = _get_session_memory()
    return _session_memory_instance

def _get_working_memory_instance() -> WorkingMemory:
    global _working_memory_instance
    if _working_memory_instance is None:
        _working_memory_instance = _get_working_memory()
    return _working_memory_instance

def _get_longterm_memory_instance() -> LongTermMemory:
    global _longterm_memory_instance
    if _longterm_memory_instance is None:
        _longterm_memory_instance = _get_longterm_memory()
    return _longterm_memory_instance


@router.get("/session/{session_id}", response_model=SessionHistoryResponse)
async def get_session_memory(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip")
):
    """
    Get conversation history for a session with pagination.
    
    Returns messages in chronological order (oldest first).
    """
    try:
        # Get session with proper configuration
        session_memory = _get_session_memory_instance()
        
        # Get session
        session = await session_memory.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Apply pagination
        total_messages = len(session.messages)
        paginated_messages = session.messages[offset:offset + limit]
        has_more = (offset + limit) < total_messages
        
        return SessionHistoryResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            message_count=total_messages,
            messages=paginated_messages,
            has_more=has_more
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session memory", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.get("/working", response_model=WorkingMemoryResponse)
async def get_working_memory(
    user_id: str = Query(..., description="User ID to filter by"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page")
):
    """
    Get recent working memory entries (7-30 days retention).
    
    Returns active context and recent information.
    """
    try:
        # Get working memory with proper configuration
        working_memory = _get_working_memory_instance()
        
        # Get entries with filtering
        if memory_type:
            entries = await working_memory.get_by_type(user_id, memory_type, limit=page_size * page)
        else:
            entries = await working_memory.get_recent(user_id, limit=page_size * page)
        
        # Apply pagination
        offset = (page - 1) * page_size
        paginated_entries = entries[offset:offset + page_size]
        
        return WorkingMemoryResponse(
            entries=paginated_entries,
            total_count=len(entries),
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error("Failed to get working memory", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve working memory: {str(e)}")


@router.get("/longterm", response_model=LongTermMemoryResponse)
async def get_longterm_memory(
    user_id: str = Query(..., description="User ID to filter by"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    min_importance: float = Query(0.0, ge=0.0, le=1.0, description="Minimum importance score"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page")
):
    """
    Get long-term memory entries (permanent knowledge).
    
    Returns consolidated facts ordered by importance.
    """
    try:
        # Get longterm memory with proper configuration
        longterm_memory = _get_longterm_memory_instance()
        
        # Get entries with filtering
        if memory_type:
            entries = await longterm_memory.get_by_type(user_id, memory_type, limit=page_size * page)
        else:
            entries = await longterm_memory.get_important(user_id, min_importance=min_importance, limit=page_size * page)
        
        # Apply pagination
        offset = (page - 1) * page_size
        paginated_entries = entries[offset:offset + page_size]
        
        return LongTermMemoryResponse(
            entries=paginated_entries,
            total_count=len(entries),
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error("Failed to get longterm memory", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve long-term memory: {str(e)}")


@router.get("/stats/{user_id}", response_model=MemoryStatsResponse)
async def get_memory_stats(user_id: str):
    """
    Get memory statistics and metrics for a user.
    
    Returns counts and aggregate metrics across memory layers.
    """
    try:
        # Get memory instances with proper configuration
        working_memory = _get_working_memory_instance()
        longterm_memory = _get_longterm_memory_instance()
        
        # Count entries in each layer
        working_entries = await working_memory.get_recent(user_id, limit=1000)
        longterm_entries = await longterm_memory.get_important(user_id, min_importance=0.0, limit=1000)
        
        # Calculate average importance if available
        avg_importance = None
        if longterm_entries:
            importance_scores = [e.importance_score for e in longterm_entries if hasattr(e, 'importance_score')]
            if importance_scores:
                avg_importance = sum(importance_scores) / len(importance_scores)
        
        return MemoryStatsResponse(
            user_id=user_id,
            working_memory_count=len(working_entries),
            longterm_memory_count=len(longterm_entries),
            total_memories=len(working_entries) + len(longterm_entries),
            avg_importance=avg_importance
        )
    except Exception as e:
        logger.error("Failed to get memory stats", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory stats: {str(e)}")
