from typing import Optional, List, Dict, Any
from .models import AssembledContext, SessionMessage, WorkingMemoryEntry, LongTermMemoryEntry
from .session_memory import SessionMemory
from .working_memory import WorkingMemory
from .long_term_memory import LongTermMemory

class ContextAssembler:
    """
    The 'brain' that assembles context from all memory layers.
    Follows a priority-based token budget approach.
    """
    async def _build_context(
        self,
        session_msgs: List[SessionMessage],
        working_entries: List[WorkingMemoryEntry],
        longterm_entries: List[LongTermMemoryEntry],
        max_tokens: int,
        status: str = "healthy"
    ) -> AssembledContext:
        """
        Build context from memory components.
        Used by ResilientContextAssembler.
        """
        # Convert to dict format for the new AssembledContext structure
        selected_msgs = []
        selected_facts = []
        total_tokens = 0
        source_counts = {"session": 0, "working": 0, "longterm": 0}
        remaining_tokens = max_tokens
        
        # Add session messages
        for msg in session_msgs:
            msg_dict = {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()}
            msg_tokens = self.estimate_object_tokens(msg_dict)
            if remaining_tokens - msg_tokens > 0:
                selected_msgs.append(msg_dict)
                total_tokens += msg_tokens
                remaining_tokens -= msg_tokens
                source_counts["session"] += 1
        
        # Add working memory entries
        for entry in working_entries:
            entry_dict = {
                "type": entry.memory_type,
                "content": entry.content,
                "metadata": entry.metadata,
                "timestamp": entry.created_at.isoformat()
            }
            entry_tokens = self.estimate_object_tokens(entry_dict)
            if remaining_tokens - entry_tokens > 1000:  # Keep reserve
                selected_facts.append(entry_dict)
                total_tokens += entry_tokens
                remaining_tokens -= entry_tokens
                source_counts["working"] += 1
        
        # Add long-term memory facts
        for fact in longterm_entries:
            fact_dict = {
                "type": fact.memory_type,
                "content": fact.content,
                "importance": fact.importance,
                "metadata": fact.metadata
            }
            fact_tokens = self.estimate_object_tokens(fact_dict)
            if remaining_tokens - fact_tokens > 0:
                selected_facts.append(fact_dict)
                total_tokens += fact_tokens
                remaining_tokens -= fact_tokens
                source_counts["longterm"] += 1
        
        return AssembledContext(
            messages=selected_msgs,
            facts=selected_facts,
            total_tokens=total_tokens,
            source_counts=source_counts,
            status=status
        )

    def __init__(
        self,
        session_memory: Optional[SessionMemory] = None,
        working_memory: Optional[WorkingMemory] = None,
        long_term_memory: Optional[LongTermMemory] = None
    ):
        self.session_memory = session_memory or SessionMemory()
        self.working_memory = working_memory or WorkingMemory()
        self.long_term_memory = long_term_memory or LongTermMemory()
        
    def estimate_tokens(self, text: str) -> int:
        """Simple token estimation: 1 token ≈ 4 characters in English."""
        return len(text) // 4
        
    def estimate_object_tokens(self, obj) -> int:
        """Estimate tokens for a Pydantic model or dict."""
        # If it's a Pydantic model, use model_dump_json
        if hasattr(obj, 'model_dump_json'):
            text = obj.model_dump_json()
        else:
            import json
            text = json.dumps(obj)
        return self.estimate_tokens(text)
        
    async def assemble_context(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        max_tokens: int = 8000
    ) -> AssembledContext:
        """
        Assemble context from all memory layers.
        
        Priority:
        1. Session Memory (always include)
        2. Working Memory (recent context)
        3. Long-Term Memory (important facts)
        """
        context = AssembledContext()
        remaining_tokens = max_tokens
        
        # LAYER 1: Session Memory (highest priority - always included)
        if session_id:
            session = await self.session_memory.get_session(session_id)
            if session:
                context.session = session
                session_tokens = self.estimate_object_tokens(session)
                remaining_tokens -= session_tokens
                
        # LAYER 2: Working Memory (recent context)
        if remaining_tokens > 2000:
            recent = await self.working_memory.get_recent(
                user_id=user_id,
                limit=10
            )
            # Calculate tokens for each memory and add until budget exhausted
            for memory in recent:
                memory_tokens = self.estimate_object_tokens(memory)
                if remaining_tokens - memory_tokens > 1000:  # Keep 1000 reserve
                    context.recent_memories.append(memory)
                    remaining_tokens -= memory_tokens
                else:
                    break
                    
        # LAYER 3: Long-Term Memory (important facts)
        if remaining_tokens > 1000:
            facts = await self.long_term_memory.get_important(
                user_id=user_id,
                min_importance=0.7,
                limit=5
            )
            for fact in facts:
                fact_tokens = self.estimate_object_tokens(fact)
                if remaining_tokens - fact_tokens > 0:
                    context.facts.append(fact)
                    remaining_tokens -= fact_tokens
                    # Update access tracking
                    await self.long_term_memory.update_access(fact.id)
                else:
                    break
                    
        # Calculate total tokens used
        context.total_tokens = max_tokens - remaining_tokens
        
        return context
