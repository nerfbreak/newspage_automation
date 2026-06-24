# Workspace Customizations

## AI-Facing Project Memory System

To maintain context across sessions and avoid hallucinations, you (and any sub-agents you invoke) MUST adhere to the following rules:

1. **Read the Memory:** Always review the contents of `docs/memory/` (specifically `STATE.md`, `CONTEXT.md`, and `DECISIONS.md`) when starting a new task or session.
2. **Update the State:** Whenever a task is completed or the current focus shifts, update `docs/memory/STATE.md` to reflect the new reality.
3. **Log Decisions:** If you make a significant architectural, design, or technical decision, add an entry to `docs/memory/DECISIONS.md`.
4. **Delegate with Context:** When invoking sub-agents, instruct them to read `docs/memory/` first so they understand the project's background.
