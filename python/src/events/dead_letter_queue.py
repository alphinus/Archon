"""
Event Reliability Layer.
Dead Letter Queue for failed events.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from structlog import get_logger
from supabase import create_client, Client
import os

logger = get_logger(__name__)

class DeadLetterQueue:
    """
    Stores and manages failed events.
    Provides automatic retry with exponential backoff.
    """
    
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        self.table_name = "event_failures"
        
    async def record_failure(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        error: Exception,
        user_id: Optional[str] = None
    ):
        """Record a failed event."""
        try:
            import traceback
            
            data = {
                "event_id": event_id,
                "event_type": event_type,
                "payload": payload,
                "user_id": user_id,
                "error_message": str(error),
                "stack_trace": traceback.format_exc(),
                "retry_count": 0,
                "next_retry_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            self.client.table(self.table_name).insert(data).execute()
            
            logger.warning(
                "event_failed_recorded",
                event_id=event_id,
                event_type=event_type,
                error=str(error)
            )
            
        except Exception as e:
            # Even DLQ can fail - log but don't crash
            logger.error("dlq_record_failed", error=str(e))
    
    async def get_pending_retries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events that are due for retry."""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("status", "pending")\
                .lte("next_retry_at", datetime.now().isoformat())\
                .lt("retry_count", 3)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error("dlq_get_pending_failed", error=str(e))
            return []
    
    async def mark_retry_attempt(
        self,
        failure_id: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Mark a retry attempt."""
        try:
            if success:
                # Mark as resolved
                self.client.table(self.table_name)\
                    .update({
                        "status": "resolved",
                        "resolved_at": datetime.now().isoformat()
                    })\
                    .eq("id", failure_id)\
                    .execute()
                
                logger.info("event_retry_succeeded", failure_id=failure_id)
            else:
                # Increment retry count and schedule next attempt
                failure = self.client.table(self.table_name)\
                    .select("retry_count")\
                    .eq("id", failure_id)\
                    .single()\
                    .execute()
                
                retry_count = failure.data["retry_count"] + 1
                
                if retry_count >= 3:
                    # Max retries reached
                    status = "failed"
                    next_retry = None
                else:
                    # Exponential backoff: 5min, 30min, 2h
                    backoff_minutes = [5, 30, 120][retry_count]
                    status = "pending"
                    next_retry = (datetime.now() + timedelta(minutes=backoff_minutes)).isoformat()
                
                self.client.table(self.table_name)\
                    .update({
                        "retry_count": retry_count,
                        "last_retry_at": datetime.now().isoformat(),
                        "next_retry_at": next_retry,
                        "status": status,
                        "error_message": error
                    })\
                    .eq("id", failure_id)\
                    .execute()
                
                logger.warning(
                    "event_retry_failed",
                    failure_id=failure_id,
                    retry_count=retry_count,
                    status=status
                )
            
            # Log the attempt
            self.client.table("event_replay_log").insert({
                "event_failure_id": failure_id,
                "success": success,
                "error_message": error
            }).execute()
            
        except Exception as e:
            logger.error("dlq_mark_retry_failed", error=str(e))
    
    async def get_failed_events(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get permanently failed events for manual inspection."""
        try:
            query = self.client.table(self.table_name)\
                .select("*")\
                .eq("status", "failed")\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error("dlq_get_failed_events_error", error=str(e))
            return []
    
    async def cleanup_old_resolved(self, days: int = 30):
        """Clean up old resolved events."""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.client.table(self.table_name)\
                .delete()\
                .eq("status", "resolved")\
                .lt("resolved_at", cutoff)\
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info("dlq_cleanup_completed", deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("dlq_cleanup_failed", error=str(e))
            return 0
