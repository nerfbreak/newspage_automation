# Spec Kit Artifact Policy

**Status**: Active project policy  
**Last reviewed**: 2026-07-07

This repository intentionally ignores most local Spec Kit and agent workspace folders:

- `.agents/`
- `.specify/`
- `specs/`

That is acceptable because many files in those folders are local workflow state, scratch planning, or agent-only context. It also means important project memory can exist on disk without automatically entering git.

## What Must Be Tracked

Track durable artifacts when they affect future maintenance, production readiness, or team handoff:

- Root `AGENTS.md` instructions.
- `.agents/MEMORY.md` when a completed task changes project knowledge.
- `.specify/memory/plan.md` references in `AGENTS.md` when the consolidated plan changes.
- Security, migration, regression, and production-readiness docs under `docs/`.
- Feature specs only when they are intended to be reviewed from git.

Because `.agents/`, `.specify/`, and `specs/` are ignored, use `git add -f` only for the specific artifact that must be preserved. Do not force-add whole directories.

## What Must Stay Local

Keep these out of git unless the user explicitly decides otherwise:

- Agent scratch files.
- Temporary feature plans that were superseded.
- Local-only skill caches.
- Any artifact containing secrets, credentials, screenshots, or portal data.

## Review Checklist

Before a checkpoint commit:

- Confirm required docs are tracked or force-staged intentionally.
- Confirm no local secrets are staged.
- Confirm ignored Spec Kit artifacts are either documented as local-only or force-added individually.
- Update `.agents/MEMORY.md` after successful implementation, verification, or production-readiness changes.
