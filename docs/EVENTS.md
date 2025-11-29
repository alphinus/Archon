# ⚡ Archon Real-Time Event System

## Overview

Archon uses a **Real-Time Memory Sync Engine** powered by Postgres `LISTEN/NOTIFY`. This enables:
1. **Instant Synchronization**: When one agent learns something, all others know immediately.
2. **Decoupled Architecture**: Services communicate via events, not direct calls.
3. **Reliability**: Events are transactional - if the database commit fails, the event isn't sent.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHON REAL-TIME ENGINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ Agent A      │         │ Agent B      │                     │
│  │ Creates Fact │────┬───▶│ Notified!    │                     │
│  └──────────────┘    │    └──────────────┘                     │
│                      │                                           │
│                      ▼                                           │
│            ┌─────────────────────┐                              │
│            │  EVENT BUS          │                              │
│            │  (Postgres NOTIFY)  │                              │
│            └─────────────────────┘                              │
│                      │                                           │
│                      ▼                                           │
│            ┌─────────────────────┐                              │
│            │ BACKGROUND WORKERS  │                              │
│            │  - Memory Cleanup   │                              │
│            │  - Consolidation    │                              │
│            └─────────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Event Types

| Event Type | Description | Payload |
|------------|-------------|---------|
| `memory.working.created` | New short-term memory | `memory_id`, `content`, `type` |
| `memory.longterm.created` | New permanent fact | `memory_id`, `content`, `importance` |
| `system.cleanup.triggered` | Maintenance ran | `worker`, `deleted_count` |

## Usage

### Publishing Events

Events are automatically published by Memory services, but you can publish custom events:

```python
from src.events import get_event_bus, EventType

bus = get_event_bus()
await bus.publish(
    "custom.event",
    payload={"message": "Hello World"},
    user_id="user123"
)
```

### Subscribing to Events

```python
async def my_handler(payload):
    print(f"Received: {payload}")

bus = get_event_bus()
await bus.start_listening()
bus.subscribe(EventType.MEMORY_WORKING_CREATED, my_handler)
```

## Background Workers

Archon includes built-in workers that react to events and schedules:

1. **MemoryConsolidator**: Promotes high-value Working Memory to Long-Term Memory.
2. **CleanupWorker**: Removes expired memories and decays importance scores.

Run workers:
```bash
python -m src.workers.runner
```

## Configuration

The Event Bus uses the standard Supabase credentials from `.env`:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

No additional infrastructure (Redis/Kafka) is required.
