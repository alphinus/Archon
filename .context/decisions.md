# Architectural Decisions Log

## [2025-12-01] AI Context Standardization
**Decision:** Implement a standardized file structure (`AI_WORK_LOG.md`, `AI_TASKS.md`, `.context/`) to ensure context preservation across different AI models and sessions.
**Rationale:** To prevent knowledge loss and ensure consistent project state tracking regardless of the AI agent used.

## [2025-12-01] Git Hygiene
**Decision:** Enforce strict `.gitignore` rules to prevent nested `.git` repositories.
**Rationale:** Nested repositories cause confusion and version control issues.
