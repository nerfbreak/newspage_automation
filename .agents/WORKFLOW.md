# Cross-Agent Workflow

This repository is maintained across Codex, Antigravity, and Hermes. Treat the repository files as the official shared memory. Tool-specific persistent memory is helpful, but it is not authoritative.

## Goal

Keep every AI agent aligned on the same product context, locked rules, active work, and next steps so work can move between tools without changing architecture, style, or behavior unexpectedly.

## Source of Truth Order

Read these files in this order before changing anything:

1. `AGENTS.md`
2. `.agents/MEMORY.md`
3. `.agents/CURRENT_HANDOFF.md`
4. `product_requirements_document.md`
5. Active Spec Kit files under `specs/` when the handoff or `AGENTS.md` points to one
6. Relevant source files for the requested task

If tool memory conflicts with repository files, the repository files win.

## Start-of-Session Protocol

Every agent must do this at the start of a work session:

1. Check git status and identify uncommitted work.
2. Read the source-of-truth files listed above.
3. Confirm the current branch and active feature/spec.
4. Check `.agents/CURRENT_HANDOFF.md` for the last known status.
5. Avoid editing files with unrelated user or agent changes.
6. If the task touches a locked feature, ask for the unlock password before making changes.

Use `.agents/templates/START_SESSION.md` as the preferred note format when an agent needs to report readiness before working.

## Finish/Handoff Protocol

Every agent must do this before ending a work session:

1. Update `.agents/CURRENT_HANDOFF.md` with the real current state.
2. Append a concise entry to `.agents/MEMORY.md` under `Changelog & Decisions`.
3. Record any skipped tests, failed checks, manual follow-ups, or Supabase changes needed.
4. Commit only when the active workflow requires it or the user asks for it.
5. Leave enough detail that another agent can continue without asking what happened.

Use `.agents/templates/FINISH_HANDOFF.md` as the preferred handoff format.

## Work Ownership Rules

- Do not rewrite frozen business logic unless the user explicitly unlocks it with the project password.
- Do not refactor unrelated files while solving a narrow task.
- Do not guess Newspage selectors. Use the documented selector source and existing code.
- Do not introduce UI outside the locked Neo-Brutalism design system.
- Do not treat `CHANGELOG.md` as an internal engineering log. It is user-facing only.
- Prefer additive docs and small scoped patches over broad cleanups.

## Branch and Commit Hygiene

- Use a focused branch for feature work.
- Pull or sync before continuing work in another tool.
- Commit meaningful checkpoints when a task is complete and verified.
- Do not mix unrelated fixes into one commit.
- If another tool has uncommitted work, preserve it and coordinate through `.agents/CURRENT_HANDOFF.md`.

## Memory Discipline

`.agents/MEMORY.md` is for durable decisions and completed work. It should not become a scratchpad.

Good entries include:

- Completed feature or bug fix summary
- Locked design or architecture decision
- Required external action, such as a Supabase migration
- Important operational caveat learned during implementation

Avoid:

- Long command logs
- Raw stack traces unless they explain a lasting decision
- Temporary ideas that were not implemented
- Secrets, credentials, cookies, or tokens

## Handoff Quality Bar

A good handoff answers:

- What was requested?
- What has already been done?
- What files changed?
- What still needs work?
- What checks passed or were skipped?
- What must not be touched next?

If the next agent can continue from the handoff without reading chat history, the handoff is good.
