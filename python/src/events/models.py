"""
Pydantic models for events.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid

class Event(BaseModel):
    """Standard event model."""
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    payload: Dict[str, Any]
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
