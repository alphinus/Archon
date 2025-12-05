# Architectural Decisions Log

## [2025-12-04] 7-Agent Architecture

**Decision:** Implement event-driven multi-agent system with 7 specialized agents coordinated by an Orchestration Agent.

**Rationale:**

- **Separation of Concerns:** Each agent handles a specific domain (Testing, Data, DevEx, etc.)
- **Scalability:** Agents can be scaled independently based on workload
- **Resilience:** System continues operating even if individual agents fail
- **Extensibility:** New agents can be added without modifying existing ones
- **Testability:** Each agent can be tested in isolation

**Architecture:**

- **BaseAgent Framework:** Shared infrastructure for event handling, skill registration, inter-agent communication
- **Event Bus (Redis):** Publish/subscribe for async agent communication with correlation IDs
- **Skill-Based System:** Each agent exposes skills that other agents can call
- **Orchestration Pattern:** Orchestration Agent coordinates multi-step workflows across agents

## [2025-12-01] AI Context Standardization

**Decision:** Implement a standardized file structure (`AI_WORK_LOG.md`, `AI_TASKS.md`, `.context/`) to ensure context preservation across different AI models and sessions.
**Rationale:** To prevent knowledge loss and ensure consistent project state tracking regardless of the AI agent used.

## [2025-12-01] Git Hygiene

**Decision:** Enforce strict `.gitignore` rules to prevent nested `.git` repositories.
**Rationale:** Nested repositories cause confusion and version control issues.
