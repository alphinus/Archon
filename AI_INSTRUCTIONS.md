# 🤖 AI PROTOCOL & INSTRUCTIONS

**STOP! READ THIS FIRST.**

This file is the **MANDATORY INITIALIZATION PROTOCOL** for any AI agent (Claude, GPT, Gemini, etc.) working on this repository. Failure to follow these steps will result in context loss and project degradation.

---

## 🚀 1. Initialization Sequence (Do this IMMEDIATELY)

Before writing a single line of code or answering a complex question, you **MUST** read the following files to load the project state into your context:

1.  **📄 `AI_WORK_LOG.md`**
    *   *Why:* Understand what happened last. Who worked on what? What was the outcome?
    *   *Action:* Read the last 2-3 entries.

2.  **📋 `AI_TASKS.md`**
    *   *Why:* Know the current priorities. What is P0? What is In Progress?
    *   *Action:* Identify the task you are about to work on.

3.  **📂 `.context/current_state.md`**
    *   *Why:* Know the system health. Is the server down? Is the UI broken?
    *   *Action:* Check for "Active Issues".

4.  **📂 `.context/decisions.md`**
    *   *Why:* Understand *why* things are built this way.
    *   *Action:* Respect architectural decisions (e.g., "No nested .git").

---

## 📝 2. Documentation Rules (During & After Work)

You are responsible for maintaining the project's memory.

### A. Update `AI_WORK_LOG.md`
*   **When:** At the start (Goal) and end (Status) of your session.
*   **Format:**
    ```markdown
    ## [YYYY-MM-DD HH:MM] Session by [Model Name]
    **Goal:** [One sentence summary]
    **Changes:**
    - [MODIFY] file/path
    - [NEW] file/path
    **Status:** [Completed/In Progress/Failed] - [Brief result]
    ```

### B. Update `AI_TASKS.md`
*   **When:** You start a task or finish one.
*   **Action:** Move items between `[ ]` (Todo), `[/]` (In Progress), and `[x]` (Done).

### C. Update `.context/current_state.md`
*   **When:** You fix a bug or break something.
*   **Action:** Update the "Status" and "Active Issues" section.

---

## 🛡️ 3. Critical Safety Rules

1.  **NO Nested Git Repositories:**
    *   Never run `git init` inside a subdirectory.
    *   Never create a `.git` folder anywhere except the root.
    *   *Check:* `find . -name ".git"` before assuming.

2.  **Respect `CONTRIBUTING.md`:**
    *   Follow the project's coding standards (Python/React).
    *   No direct imports between microservices.

3.  **Idempotency:**
    *   Assume your session might crash. Write files in a way that the next agent can pick up where you left off (using the Log and Tasks).

---

**By following this protocol, you ensure that Archon remains a robust, state-of-the-art system, regardless of which AI model is currently operating it.**
