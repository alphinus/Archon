# 🧠 Archon Memory System

## Overview

Archon features a **4-layer memory architecture** that gives AI agents true persistent memory across sessions. The system automatically injects relevant context into every agent request without manual intervention.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Request                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          AAL (Agent Abstraction Layer)                │  │
│  │     ⬇️ Automatic Memory Injection ⬇️                  │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │       Context Assembler                      │    │  │
│  │  │  (Unifies all memory layers)                │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │          ⬆️          ⬆️           ⬆️                  │  │
│  └──────────┼──────────┼───────────┼──────────────────┘  │
│            │          │           │                       │
│     ┌──────┴───┐  ┌──┴──────┐  ┌─┴────────┐             │
│     │ Session  │  │ Working │  │Long-Term │             │
│     │  Memory  │  │ Memory  │  │  Memory  │             │
│     │ (Redis)  │  │(Postgres)│  │(Postgres)│             │
│     │  1 hour  │  │7-30 days│  │Permanent │             │
│     └──────────┘  └─────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Memory Layers

### 1. Session Memory (Redis)
- **Purpose**: Real-time conversation context
- **Lifespan**: 1 hour TTL
- **Storage**: Redis
- **Use Case**: Current conversation messages

### 2. Working Memory (Postgres)
- **Purpose**: Recent activity and decisions
- **Lifespan**: 7-30 days (configurable)
- **Storage**: PostgreSQL with automatic cleanup
- **Types**: `conversation`, `action`, `decision`

### 3. Long-Term Memory (Postgres)
- **Purpose**: Permanent knowledge base
- **Lifespan**: Unlimited (until manually deleted)
- **Storage**: PostgreSQL with importance scoring
- **Types**: `fact`, `preference`, `skill`, `relationship`

### 4. Context Assembler
- **Purpose**: Intelligent context retrieval
- **Algorithm**: Priority-based token budget
- **Output**: Unified context from all 3 layers

## Quick Start

### Run the Live Demo

See the memory system in action:

```bash
cd python
uv run --with supabase --with redis --with python-dotenv ../demo_memory_live.py
```

This demo shows:
- ✅ Memory creation across all 3 layers
- ✅ Context assembly with token budget
- ✅ AAL automatic injection
- ✅ Cross-session persistence

### Prerequisites

Ensure these services are running:
- Redis (via docker-compose)
- Supabase (with V5 migration applied)

## API Usage

### Basic Memory Operations

```python
from src.memory import SessionMemory, WorkingMemory, LongTermMemory, Message

# Session Memory
sm = SessionMemory()
await sm.connect()
session = await sm.create_session(user_id="user123", session_id="session456")
await sm.add_message("session456", Message(role="user", content="Hello!"))

# Working Memory
wm = WorkingMemory()
await wm.create(
    user_id="user123",
    memory_type="action",
    content={"action": "created_feature", "status": "complete"},
    ttl_days=7
)

# Long-Term Memory
ltm = LongTermMemory()
await ltm.create(
    user_id="user123",
    memory_type="preference",
    content={"preference": "User prefers TypeScript over JavaScript"},
    importance_score=0.9
)
```

### Context Assembly

```python
from src.memory import ContextAssembler

assembler = ContextAssembler()
context = await assembler.assemble_context(
    user_id="user123",
    session_id="session456",
    max_tokens=4000  # Token budget
)

print(f"Session messages: {len(context.session.messages)}")
print(f"Recent memories: {len(context.recent_memories)}")
print(f"Facts: {len(context.facts)}")
print(f"Total tokens used: {context.total_tokens}")
```

### AAL Integration (Automatic)

Memory injection happens automatically when using AAL:

```python
from src.aal.models import AgentRequest
from src.aal.service import get_agent_service

# Create request with memory parameters
request = AgentRequest(
    prompt="What do you know about my project?",
    user_id="user123",      # Required for memory
    session_id="session456", # Optional but recommended
    enable_memory=True       # Default: True
)

# Memory is automatically injected before routing to AI provider
agent_service = get_agent_service()
response = await agent_service.execute_request(request)
```

**What happens automatically:**
1. `ContextAssembler` retrieves memories from all 3 layers
2. Context is formatted as system message
3. Prepended to `conversation_history`
4. Agent receives full context without manual work

## Configuration

### Memory Token Budget

Control how much context is included:

```python
request = AgentRequest(
    prompt="...",
    user_id="user123",
    memory_max_tokens=2000  # Default: 4000
)
```

### Disable Memory for Specific Requests

```python
request = AgentRequest(
    prompt="Simple calculation: 2+2",
    enable_memory=False  # Skip memory injection
)
```

## Database Schema

### Migration

Apply the V5 migration in Supabase SQL Editor:

```bash
migration/V5_memory_system.sql
```

This creates:
- `working_memory` table with TTL
- `long_term_memory` table
- Cleanup functions

## Verification

Run all verification scripts:

```bash
# Session Memory (Redis)
cd python && uv run --with redis --with pydantic ../verify_session_memory.py

# Working & Long-Term Memory (Postgres)
cd python && uv run --with supabase --with redis --with python-dotenv ../verify_postgres_memory.py

# Context Assembler
cd python && uv run --with supabase --with redis --with python-dotenv ../verify_context_assembler.py

# AAL Integration
cd python && uv run --with pydantic ../verify_aal_memory_simple.py
```

## Advanced Topics

### Custom Context Assembly

Implement custom retrieval strategies:

```python
class CustomAssembler(ContextAssembler):
    async def assemble_context(self, user_id, session_id=None, max_tokens=8000):
        # Custom logic here
        context = await super().assemble_context(user_id, session_id, max_tokens)
        # Post-process context
        return context
```

### Memory Cleanup

Scheduled cleanup (run daily):

```sql
-- Clean expired working memories
SELECT cleanup_expired_working_memory();

-- Decay rarely-accessed long-term memory importance
SELECT decay_long_term_importance();
```

### Monitoring

Check memory usage:

```python
# Session Memory
session_count = await redis_client.dbsize()

# Working Memory
recent_count = await wm.get_recent(user_id, limit=1000)

# Long-Term Memory
facts = await ltm.get_important(user_id, min_importance=0.5)
```

## Troubleshooting

### Memory not injecting

1. Check `user_id` is provided in request
2. Verify `enable_memory=True` (default)
3. Ensure Redis is running
4. Confirm Supabase migration applied

### Context too large

Reduce token budget:
```python
request.memory_max_tokens = 2000
```

### Memory persistence issues

- Session Memory: Check Redis connection
- Working/Long-Term: Verify Supabase credentials
- Check logs for errors

## Performance

- **Session Memory**: ~10-20ms (Redis)
- **Context Assembly**: ~50-100ms (all layers)
- **Total Overhead**: < 150ms per request

## Future Enhancements

- [ ] Vector Memory (pgvector) for semantic search
- [ ] Memory consolidation (Working → Long-Term)
- [ ] Multi-user memory isolation
- [ ] Memory analytics dashboard

---

**Built with ❤️ by the Archon Team**
