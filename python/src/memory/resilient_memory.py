"""
Resilient Memory Layer.
Provides circuit breakers, retry logic, and fallbacks for the Memory System.
"""

from typing import Optional, List
from structlog import get_logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from pybreaker import CircuitBreaker, CircuitBreakerError
import asyncio

from .models import AssembledContext, SessionMessage, WorkingMemoryEntry, LongTermMemoryEntry
from .session_memory import SessionMemory
from .working_memory import WorkingMemory
from .long_term_memory import LongTermMemory
from .context_assembler import ContextAssembler

logger = get_logger(__name__)

# Circuit Breakers for each service
redis_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="redis_circuit"
)

postgres_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="postgres_circuit"
)


class MemoryServiceError(Exception):
    """Base exception for memory service errors."""
    pass

class ResilientContextAssembler:
    """
    Context Assembler with circuit breakers, retry logic, and fallback strategies.
    
    Resilience Features:
    - Circuit breakers for Redis and Postgres
    - Exponential backoff retry (max 3 attempts)
    - Graceful degradation to partial context
    - Cached fallback for total failures
    """
    
    def __init__(self):
        self.session_memory = SessionMemory()
        self.working_memory = WorkingMemory()
        self.longterm_memory = LongTermMemory()
        self.assembler = ContextAssembler()
        self._context_cache = {}  # Simple in-memory cache for fallback
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, "WARNING")
    )
    async def assemble_context(
        self,
        user_id: str,
        session_id: str,
        max_tokens: int = 4000
    ) -> AssembledContext:
        """
        Assemble context with full resilience.
        
        Fallback chain:
        1. Try full context (Session + Working + LongTerm)
        2. If Redis fails: Skip session, use Working + LongTerm
        3. If Postgres fails: Use cached context
        4. If all fails: Return empty context with error status
        """
        try:
            # Try full assembly
            context = await self._assemble_full_context(user_id, session_id, max_tokens)
            
            # Cache successful result
            self._context_cache[f"{user_id}:{session_id}"] = context
            
            return context
            
        except CircuitBreakerError as e:
            logger.warning(
                "circuit_breaker_open",
                breaker=str(e),
                user_id=user_id,
                session_id=session_id
            )
            # Use cached context
            return await self._get_cached_context(user_id, session_id)
            
        except Exception as e:
            logger.error(
                "context_assembly_failed",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            # Last resort: empty context
            return AssembledContext(
                messages=[],
                facts=[],
                total_tokens=0,
                source_counts={"error": 1},
                status="error",
                error=str(e)
            )
    
    @redis_breaker
    async def _get_session_memory(self, session_id: str) -> List[SessionMessage]:
        """Get session memory with circuit breaker."""
        try:
            return await self.session_memory.get_messages(session_id)
        except Exception as e:
            logger.warning("session_memory_failed", error=str(e), session_id=session_id)
            raise MemoryServiceError(f"Session memory failed: {e}")
    
    @postgres_breaker
    async def _get_working_memory(self, user_id: str) -> List[WorkingMemoryEntry]:
        """Get working memory with circuit breaker."""
        try:
            return await self.working_memory.get_recent(user_id, limit=20)
        except Exception as e:
            logger.warning("working_memory_failed", error=str(e), user_id=user_id)
            raise MemoryServiceError(f"Working memory failed: {e}")
    
    @postgres_breaker
    async def _get_longterm_memory(self, user_id: str) -> List[LongTermMemoryEntry]:
        """Get long-term memory with circuit breaker."""
        try:
            return await self.longterm_memory.get_important(user_id, min_score=0.5, limit=50)
        except Exception as e:
            logger.warning("longterm_memory_failed", error=str(e), user_id=user_id)
            raise MemoryServiceError(f"Long-term memory failed: {e}")
    
    async def _assemble_full_context(
        self,
        user_id: str,
        session_id: str,
        max_tokens: int
    ) -> AssembledContext:
        """Attempt full context assembly with all memory layers."""
        session_msgs = []
        working_entries = []
        longterm_entries = []
        status = "healthy"
        
        # Try session memory
        try:
            session_msgs = await self._get_session_memory(session_id)
        except (MemoryServiceError, CircuitBreakerError):
            logger.warning("session_memory_degraded", session_id=session_id)
            status = "degraded"
        
        # Try working memory
        try:
            working_entries = await self._get_working_memory(user_id)
        except (MemoryServiceError, CircuitBreakerError):
            logger.warning("working_memory_degraded", user_id=user_id)
            status = "degraded"
        
        # Try long-term memory
        try:
            longterm_entries = await self._get_longterm_memory(user_id)
        except (MemoryServiceError, CircuitBreakerError):
            logger.warning("longterm_memory_degraded", user_id=user_id)
            status = "degraded"
        
        # Assemble from whatever we got
        return await self.assembler._build_context(
            session_msgs,
            working_entries,
            longterm_entries,
            max_tokens,
            status=status
        )
    
    async def _get_cached_context(
        self,
        user_id: str,
        session_id: str
    ) -> AssembledContext:
        """Get cached context as fallback."""
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in self._context_cache:
            cached = self._context_cache[cache_key]
            logger.info("using_cached_context", user_id=user_id, session_id=session_id)
            # Mark as cached
            cached.status = "cached"
            return cached
        
        # No cache available
        logger.warning("no_cached_context", user_id=user_id, session_id=session_id)
        return AssembledContext(
            messages=[],
            facts=[],
            total_tokens=0,
            source_counts={},
            status="no_cache"
        )
    
    def get_circuit_status(self) -> dict:
        """Get status of all circuit breakers."""
        return {
            "redis": {
                "state": redis_breaker.current_state,
                "fail_counter": redis_breaker.fail_counter,
                "opened_at": getattr(redis_breaker, 'opened_at', None)
            },
            "postgres": {
                "state": postgres_breaker.current_state,
                "fail_counter": postgres_breaker.fail_counter,
                "opened_at": getattr(postgres_breaker, 'opened_at', None)
            }
        }
