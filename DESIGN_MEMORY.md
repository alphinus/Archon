# DESIGN DOKUMENT: Memory & Context Engineering System

**Status:** Planung | **Version:** 1.0 | **Autor:** Claude Code (Sonnet 4.5)
**Ziel:** Professionelles Memory-Management für AI-Agents im AI Empire HQ

---

## 1. VISION & PROBLEM

### Problem: Agents ohne Gedächtnis sind "dumm"

**Beispiel:**
```
User: "Analysiere mein React-Projekt und erstelle einen Refactoring-Plan"
Agent: [Analysiert] "Hier ist ein Plan: 1. TypeScript einführen, 2. State Management..."

--- 2 Stunden später ---

User: "Zeig mir den Refactoring-Plan von vorhin"
Agent: "Welchen Refactoring-Plan? Ich habe keine Erinnerung daran."
```

**Warum das scheitert:**
- ❌ Kein Session-Memory (Agent vergisst nach Response)
- ❌ Kein Working-Memory (Agent kann nicht auf vergangene Conversations zugreifen)
- ❌ Kein Long-Term-Memory (Agent lernt nicht aus Interaktionen)

### Vision: Agents mit perfektem Gedächtnis

**Ziel:**
```
User: "Analysiere mein React-Projekt und erstelle einen Refactoring-Plan"
Agent: [Speichert in Long-Term-Memory: "Project: React, Created: Refactoring-Plan-123"]

--- 2 Stunden später ---

User: "Zeig mir den Refactoring-Plan von vorhin"
Agent: [Lädt aus Memory] "Hier ist der Plan von 14:30 Uhr: 1. TypeScript einführen..."

--- 1 Woche später ---

User: "Wie ist der Status des Refactorings?"
Agent: [Context aus Long-Term-Memory] "Basierend auf deinen letzten Tasks (Plan-123, Task-45, Task-46)
       hast du 2/5 Schritte abgeschlossen. Nächster Schritt: State Management."
```

---

## 2. MEMORY-ARCHITEKTUR (4-SCHICHT-MODELL)

### Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT REQUEST                             │
│  "Zeig mir den Refactoring-Plan von heute morgen"               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT ASSEMBLER                              │
│  Sammelt relevanten Context aus allen Memory-Schichten          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│   SESSION    │ │   WORKING   │ │  LONG-TERM   │ │   VECTOR    │
│    MEMORY    │ │   MEMORY    │ │    MEMORY    │ │   MEMORY    │
│              │ │             │ │              │ │             │
│  Current     │ │  Today/     │ │  All Time    │ │  Semantic   │
│  Convo       │ │  This Week  │ │  (Indexed)   │ │  Search     │
└──────────────┘ └─────────────┘ └──────────────┘ └─────────────┘
     Redis          PostgreSQL       PostgreSQL        pgvector
   (In-Memory)      (Hot Data)      (Cold Storage)    (Embeddings)
```

---

## 3. MEMORY-SCHICHTEN IM DETAIL

### 3.1 SESSION MEMORY (Redis - In-Memory)

**Zweck:** Aktuelles Gespräch in Echtzeit

**Lebensdauer:** Bis Session endet (oder 1 Stunde Inaktivität)

**Datenstruktur:**
```python
{
  "session_id": "sess_abc123",
  "user_id": "user_xyz",
  "started_at": "2025-11-28T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "Analysiere mein React-Projekt",
      "timestamp": "2025-11-28T10:30:15Z"
    },
    {
      "role": "agent",
      "content": "Ich habe 45 Komponenten gefunden...",
      "timestamp": "2025-11-28T10:30:45Z",
      "metadata": {
        "tokens_used": 2500,
        "cost_usd": 0.025,
        "provider": "anthropic"
      }
    }
  ],
  "context": {
    "active_project_id": "proj_123",
    "active_task_ids": ["task_45", "task_46"],
    "mentioned_files": ["src/App.tsx", "src/components/Header.tsx"]
  }
}
```

**Storage:** Redis Hash
```bash
redis> HSET session:sess_abc123 messages '[...]'
redis> EXPIRE session:sess_abc123 3600  # 1 Stunde TTL
```

**Vorteile:**
- ⚡ Ultra-schnell (In-Memory)
- ✅ Kein Persistence-Overhead
- ✅ Automatisches Cleanup (TTL)

---

### 3.2 WORKING MEMORY (PostgreSQL - Hot Data)

**Zweck:** Kontext der letzten Tage/Wochen (häufig genutzt)

**Lebensdauer:** 7-30 Tage (konfigurierbar)

**Datenstruktur:**
```sql
CREATE TABLE working_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(50),
    memory_type VARCHAR(50) NOT NULL,  -- 'conversation', 'action', 'decision'
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    relevance_score FLOAT DEFAULT 1.0,  -- Kann abklingen über Zeit

    INDEX idx_user_type_created (user_id, memory_type, created_at DESC),
    INDEX idx_expires (expires_at)
);
```

**Beispiel-Einträge:**
```json
// Conversation Memory
{
  "id": "mem_456",
  "user_id": "user_xyz",
  "session_id": "sess_abc123",
  "memory_type": "conversation",
  "content": {
    "summary": "User requested React project analysis, Agent found 45 components,
                identified 3 refactoring opportunities",
    "key_entities": ["React", "Refactoring", "TypeScript"],
    "artifacts": ["refactoring-plan-123"]
  },
  "metadata": {
    "session_duration_seconds": 450,
    "messages_count": 12,
    "total_cost_usd": 0.15
  },
  "created_at": "2025-11-28T11:00:00Z",
  "expires_at": "2025-12-05T11:00:00Z",  // 7 Tage später
  "relevance_score": 1.0
}

// Action Memory
{
  "id": "mem_457",
  "user_id": "user_xyz",
  "memory_type": "action",
  "content": {
    "action": "created_work_order",
    "target": "work_order_789",
    "description": "Implement TypeScript conversion for 5 components",
    "status": "in_progress"
  },
  "created_at": "2025-11-28T14:30:00Z",
  "expires_at": "2025-12-28T14:30:00Z",  // 30 Tage (längere TTL für Actions)
  "relevance_score": 0.9
}
```

**Cleanup-Strategie:**
```python
# Täglicher Cron-Job
async def cleanup_expired_working_memory():
    await db.execute("""
        DELETE FROM working_memory
        WHERE expires_at < NOW()
        OR (relevance_score < 0.1 AND created_at < NOW() - INTERVAL '7 days')
    """)
```

---

### 3.3 LONG-TERM MEMORY (PostgreSQL - Cold Storage)

**Zweck:** Permanente Wissensbasis (wie "Erinnerungen fürs Leben")

**Lebensdauer:** Unbegrenzt (bis manuell gelöscht)

**Datenstruktur:**
```sql
CREATE TABLE long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    memory_type VARCHAR(50) NOT NULL,  -- 'fact', 'preference', 'skill', 'relationship'
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    importance_score FLOAT DEFAULT 0.5,  -- 0.0 - 1.0

    INDEX idx_user_type (user_id, memory_type),
    INDEX idx_importance (user_id, importance_score DESC)
);
```

**Beispiel-Einträge:**
```json
// Fact Memory (Wissen über Projekte)
{
  "id": "ltm_100",
  "user_id": "user_xyz",
  "memory_type": "fact",
  "content": {
    "fact": "User's main project 'Archon' is a React+TypeScript+Python app",
    "entities": ["Archon", "React", "TypeScript", "Python", "FastAPI"],
    "relationships": {
      "tech_stack": ["React 18", "TanStack Query", "FastAPI", "Supabase"],
      "architecture": "Microservices with Vertical Slices"
    }
  },
  "metadata": {
    "source": "analysis_session_sess_abc123",
    "confidence": 0.95
  },
  "created_at": "2025-11-28T11:00:00Z",
  "last_accessed_at": "2025-11-28T15:30:00Z",
  "access_count": 5,
  "importance_score": 0.9
}

// Preference Memory (User-Präferenzen)
{
  "id": "ltm_101",
  "user_id": "user_xyz",
  "memory_type": "preference",
  "content": {
    "preference": "User prefers TypeScript over JavaScript",
    "context": "Multiple conversations showed consistent preference for type-safety",
    "evidence": [
      "Requested TypeScript conversion (sess_abc123)",
      "Asked about TypeScript best practices (sess_def456)",
      "Rejected JavaScript-only solution (sess_ghi789)"
    ]
  },
  "created_at": "2025-11-20T10:00:00Z",
  "last_accessed_at": "2025-11-28T14:30:00Z",
  "access_count": 12,
  "importance_score": 0.8
}

// Skill Memory (Was User gelernt hat)
{
  "id": "ltm_102",
  "user_id": "user_xyz",
  "memory_type": "skill",
  "content": {
    "skill": "React TanStack Query v5 Patterns",
    "proficiency_level": "intermediate",
    "learned_at": "2025-11-15",
    "evidence": "Successfully implemented query patterns in Archon project",
    "knowledge_gaps": [
      "Optimistic updates with rollback",
      "Parallel queries with dependencies"
    ]
  },
  "importance_score": 0.7
}
```

**Importance Decay:**
```python
# Wöchentlicher Job: Reduziere Importance von selten genutzten Memories
async def decay_importance():
    await db.execute("""
        UPDATE long_term_memory
        SET importance_score = importance_score * 0.95
        WHERE last_accessed_at < NOW() - INTERVAL '30 days'
        AND importance_score > 0.1
    """)
```

---

### 3.4 VECTOR MEMORY (pgvector - Semantic Search)

**Zweck:** Semantische Suche über alle Memory-Typen

**Use-Case:**
```
User: "Was habe ich letzte Woche über TypeScript besprochen?"

→ Vector-Search findet ALLE Memories mit "TypeScript"-Semantik:
  - Session Memory: "TypeScript conversion discussion"
  - Working Memory: "Work Order: TypeScript migration"
  - Long-Term Memory: "Preference: Loves TypeScript"
```

**Datenstruktur:**
```sql
CREATE TABLE memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL,  -- Reference zu Session/Working/LongTerm
    memory_table VARCHAR(50) NOT NULL,  -- 'session_memory', 'working_memory', 'long_term_memory'
    user_id UUID NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 oder Anthropic Embeddings
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user (user_id)
);

-- pgvector Index für schnelle Similarity-Search
CREATE INDEX idx_embedding ON memory_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Semantic Search Query:**
```python
async def semantic_memory_search(user_id: str, query: str, limit: int = 10):
    # 1. Query → Embedding
    query_embedding = await get_embedding(query)

    # 2. Vector-Search
    results = await db.fetch_all("""
        SELECT
            me.memory_id,
            me.memory_table,
            me.content_text,
            me.embedding <=> $1 AS distance,
            me.metadata
        FROM memory_embeddings me
        WHERE me.user_id = $2
        ORDER BY me.embedding <=> $1  -- Cosine Distance
        LIMIT $3
    """, query_embedding, user_id, limit)

    # 3. Hydrate full Memory-Objekte
    memories = []
    for row in results:
        if row['memory_table'] == 'long_term_memory':
            memory = await db.fetch_one(
                "SELECT * FROM long_term_memory WHERE id = $1",
                row['memory_id']
            )
            memories.append(memory)

    return memories
```

---

## 4. CONTEXT ASSEMBLER (Das Gehirn)

### Zweck: Intelligente Kontext-Zusammenstellung

**Problem:**
- Agent kann nicht ALLE Memories als Context nutzen (Token-Limit)
- Braucht **relevanten** Context für aktuelle Aufgabe

**Lösung: Context Assembler**

```python
class ContextAssembler:
    """Sammelt relevanten Context aus allen Memory-Schichten"""

    async def assemble_context(
        self,
        user_id: str,
        current_query: str,
        session_id: str,
        max_tokens: int = 8000
    ) -> AgentContext:
        """
        1. Session Memory (immer dabei)
        2. Working Memory (relevante Conversations/Actions)
        3. Long-Term Memory (Facts/Preferences)
        4. Vector Search (semantisch ähnliche Memories)
        """

        context = AgentContext()
        remaining_tokens = max_tokens

        # LAYER 1: Session Memory (höchste Priorität)
        session = await self.get_session_memory(session_id)
        context.add_section("current_session", session)
        remaining_tokens -= estimate_tokens(session)

        # LAYER 2: Semantic Search (relevante Memories)
        semantic_memories = await self.semantic_memory_search(
            user_id=user_id,
            query=current_query,
            limit=5
        )
        context.add_section("relevant_memories", semantic_memories)
        remaining_tokens -= estimate_tokens(semantic_memories)

        # LAYER 3: Working Memory (Recent Context)
        if remaining_tokens > 2000:
            working_mem = await self.get_working_memory(
                user_id=user_id,
                limit_tokens=remaining_tokens // 2
            )
            context.add_section("recent_context", working_mem)
            remaining_tokens -= estimate_tokens(working_mem)

        # LAYER 4: Long-Term Facts (High Importance)
        if remaining_tokens > 1000:
            facts = await self.get_important_facts(
                user_id=user_id,
                min_importance=0.7,
                limit_tokens=remaining_tokens
            )
            context.add_section("knowledge_base", facts)

        return context
```

**Beispiel-Output:**
```json
{
  "current_session": {
    "messages": [
      {"role": "user", "content": "Was war nochmal der Plan?"},
      {"role": "agent", "content": "..."}
    ]
  },
  "relevant_memories": [
    {
      "type": "working_memory",
      "content": "Refactoring-Plan für React-Projekt (2 Stunden alt)",
      "relevance": 0.95
    },
    {
      "type": "long_term_memory",
      "content": "User arbeitet an Archon (React+TypeScript)",
      "relevance": 0.87
    }
  ],
  "recent_context": [
    {
      "summary": "Heute: 3 Work Orders erstellt für TypeScript-Migration",
      "time": "vor 4 Stunden"
    }
  ],
  "knowledge_base": [
    {
      "fact": "User bevorzugt TypeScript",
      "importance": 0.8
    },
    {
      "fact": "Archon nutzt TanStack Query für State Management",
      "importance": 0.75
    }
  ]
}
```

---

## 5. IMPLEMENTIERUNGSPLAN

### Phase 1: Session Memory (Redis) - 2-3 Tage

**Neue Dateien:**
- `python/src/memory/__init__.py`
- `python/src/memory/session_memory.py` - Redis-basiertes Session-Tracking
- `python/src/memory/models.py` - Pydantic-Models für Memory-Strukturen

**Features:**
- Session erstellen/beenden
- Messages hinzufügen
- Context speichern (active_project, active_tasks)
- Auto-Expire nach 1h Inaktivität

**Docker-Update:**
- Redis zu `docker-compose.yml` hinzufügen (Port: 6379)

---

### Phase 2: Working Memory (PostgreSQL) - 2-3 Tage

**Neue Dateien:**
- `python/src/memory/working_memory.py`
- `migration/V5_working_memory.sql`

**Features:**
- Conversation-Summaries speichern
- Action-Memories (Work Orders, Tasks created)
- Auto-Cleanup (Expiry-based)
- Relevance-Decay

---

### Phase 3: Long-Term Memory (PostgreSQL) - 2-3 Tage

**Neue Dateien:**
- `python/src/memory/long_term_memory.py`
- `migration/V6_long_term_memory.sql`

**Features:**
- Facts, Preferences, Skills speichern
- Importance-Scoring
- Access-Tracking (für Decay)

---

### Phase 4: Vector Memory (pgvector) - 2-3 Tage

**Neue Dateien:**
- `python/src/memory/vector_memory.py`
- `migration/V7_memory_embeddings.sql`

**Features:**
- Embedding-Generation (OpenAI oder Anthropic)
- Semantic-Search
- Hybrid-Search (Vector + Keyword)

---

### Phase 5: Context Assembler - 2-3 Tage

**Neue Dateien:**
- `python/src/memory/context_assembler.py`

**Features:**
- Multi-Layer-Context-Assembly
- Token-Budget-Management
- Prioritization (Session > Semantic > Working > LongTerm)

---

### Phase 6: AAL Integration - 1 Tag

**Modifikationen:**
- `python/src/aal/service.py` - Context Assembler nutzen
- Alle Agent-Requests bekommen automatisch Context

---

## 6. ERFOLGSKRITERIEN

### Memory-System ist erfolgreich, wenn:

1. **Agent erinnert sich an vergangene Conversations**
   ```
   User: "Was war nochmal der Plan von heute morgen?"
   Agent: "Du hast um 10:30 Uhr einen Refactoring-Plan für..."
   ```

2. **Agent lernt Präferenzen**
   ```
   User: "Erstelle eine neue Komponente"
   Agent: "Ich erstelle eine TypeScript-Komponente, da du TypeScript bevorzugst."
   ```

3. **Agent nutzt Projekt-Context automatisch**
   ```
   User: "Analysiere die Performance"
   Agent: [Weiß automatisch, dass "Archon" gemeint ist]
   ```

4. **Semantic Search funktioniert**
   ```
   User: "Was habe ich über State Management gelernt?"
   Agent: [Findet alle relevanten Memories über TanStack Query, Context, etc.]
   ```

---

## 7. METRIKEN & MONITORING

### Prometheus-Metriken für Memory-System:

```python
# Memory-Zugriffe
memory_access_total = Counter('memory_access_total', 'Memory accesses',
                              ['memory_type', 'operation'])

# Context Assembly Time
context_assembly_duration = Histogram('context_assembly_duration_seconds',
                                     'Time to assemble context')

# Memory Size
memory_size_bytes = Gauge('memory_size_bytes', 'Memory size',
                         ['memory_type', 'user_id'])

# Semantic Search Latency
semantic_search_latency = Histogram('semantic_search_latency_seconds',
                                   'Vector search latency')
```

---

## 8. ZUKUNFTS-FEATURES

### Phase 7: Memory-Sharing (Multi-User)

**Use-Case:** Team-Projekte

```python
# User A erstellt Memory
await long_term_memory.create(
    user_id="user_a",
    content={"fact": "Archon nutzt React 18"},
    shared_with=["user_b", "user_c"]  # Team-Members
)

# User B kann darauf zugreifen
memories = await long_term_memory.get_shared(user_id="user_b")
```

### Phase 8: Memory-Export (Portability)

**Use-Case:** Backup, Migration, Transparency

```python
# User exportiert alle Memories als JSON
export = await memory_system.export_user_memories(user_id="user_xyz")
# → memories_user_xyz_2025-11-28.json

# Kann später re-importiert werden
await memory_system.import_memories(export)
```

### Phase 9: Federated Memory (Multi-Agent-Collaboration)

**Use-Case:** Agents teilen Wissen

```
Agent A (Code-Analyzer): "Ich habe einen Performance-Issue gefunden"
→ Speichert in Shared-Memory

Agent B (Optimizer): [Liest aus Shared-Memory] "Ich optimiere den Issue"
```

---

**Erstellt:** 28. November 2025
**Bereit für Implementierung:** ✅
**Geschätzte Gesamtdauer:** 2-3 Wochen
