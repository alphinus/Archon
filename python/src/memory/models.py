from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid

class Message(BaseModel):
    """A single message in a conversation session."""
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class SessionContext(BaseModel):
    """Contextual information for a session."""
    active_project_id: Optional[str] = None
    active_task_ids: List[str] = Field(default_factory=list)
    mentioned_files: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Session(BaseModel):
    """A conversation session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = Field(default_factory=list)
    context: SessionContext = Field(default_factory=SessionContext)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Alias for compatibility
SessionMessage = Message


# ============================================================================
# WORKING MEMORY (7-30 days TTL)
# ============================================================================

class WorkingMemoryEntry(BaseModel):
    """A working memory entry (recent context, 7-30 days retention)."""
    id: Optional[str] = None
    user_id: str
    session_id: Optional[str] = None
    memory_type: str  # 'conversation', 'action', 'decision'
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    relevance_score: float = 1.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ============================================================================
# LONG-TERM MEMORY (Permanent)
# ============================================================================

class LongTermMemoryEntry(BaseModel):
    """A long-term memory entry (permanent knowledge)."""
    id: Optional[str] = None
    user_id: str
    memory_type: str  # 'fact', 'preference', 'skill', 'relationship'
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    importance_score: float = 0.5
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ============================================================================
# ASSEMBLED CONTEXT (Unified view from all memory layers)
# ============================================================================

class AssembledContext(BaseModel):
    """Assembled context from all memory layers."""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    source_counts: Dict[str, int] = Field(default_factory=dict)
    status: str = "healthy"  # healthy, degraded, cached, error
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
