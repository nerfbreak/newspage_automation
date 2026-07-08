# Current Handoff

## Active Context

- Project: Optimize Newspage Automation
- Working model: Cross-agent repo memory for Codex, Antigravity, and Hermes
- Authoritative memory files: `AGENTS.md`, `.agents/MEMORY.md`, `.agents/WORKFLOW.md`, `product_requirements_document.md`
- Active Spec Kit pointer from `AGENTS.md`: `specs/019-session-invalidation/plan.md`

## Current Status

- Cross-agent workflow documentation has been introduced so every tool reads and writes the same project memory.
- No application business logic is being changed by this handoff.
- Locked automation modules remain protected by the existing freeze rule.

## Last Completed Work

- Created the repo-level coordination plan for working across Codex, Antigravity, and Hermes.
- Selected the "structured but lightweight" workflow: shared workflow file, current handoff file, and start/finish templates.

## Next Recommended Step

When starting any new task in any AI tool:

1. Read `AGENTS.md`.
2. Read `.agents/MEMORY.md`.
3. Read `.agents/WORKFLOW.md`.
4. Read this file.
5. Read the active spec or task files referenced by the request.
6. Update this file before handing work to another tool.

## Files to Watch

- `AGENTS.md`
- `.agents/MEMORY.md`
- `.agents/WORKFLOW.md`
- `.agents/CURRENT_HANDOFF.md`
- `product_requirements_document.md`
- `specs/019-session-invalidation/`

## Blockers

- None.

## Verification Notes

- This is a documentation/process change only.
- Verified by reading the created workflow, handoff, and template files.
- No Streamlit or Playwright runtime tests are required unless later code changes are made.
