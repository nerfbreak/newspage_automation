<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/024-clear-sales-btn-color/plan.md
<!-- SPECKIT END -->

# Project AI Rules: Newspage Automation (Optimize)

## Core Memory Principle
As an AI agent working on this project, you must act as the "AI-assisted Distributed Project Memory System".
Whenever the user asks you to implement a new feature, fix a bug, or make architectural changes:
1. **READ FIRST**: Always read `.agents/MEMORY.md` and `product_requirements_document.md` to understand the current context and prevent hallucinations.
2. **UPDATE MEMORY**: After successfully completing a task, you MUST append a brief summary of what you did to `.agents/MEMORY.md` under the "Changelog & Decisions" section. Keep it concise.
3. **DO NOT GUESS**: Rely on the existing codebase files and the `elements_yang_dipakai_dinewspage_sebagai_otomasi.md` for UI selectors instead of guessing.
4. **CROSS-AGENT HANDOFF**: When work may continue in Codex, Antigravity, or Hermes, also read `.agents/WORKFLOW.md` and `.agents/CURRENT_HANDOFF.md` before making changes, then update `.agents/CURRENT_HANDOFF.md` before ending the session.

## Cross-Agent Coordination
- The repository is the official shared memory for Codex, Antigravity, and Hermes. Tool-specific persistent memory is secondary.
- Before starting work, follow `.agents/WORKFLOW.md` and use `.agents/templates/START_SESSION.md` as the preferred readiness format when needed.
- Before handing work to another tool, update `.agents/CURRENT_HANDOFF.md` and use `.agents/templates/FINISH_HANDOFF.md` as the preferred handoff format.
- If tool memory conflicts with `AGENTS.md`, `.agents/MEMORY.md`, `.agents/WORKFLOW.md`, or active Spec Kit files, the repository files win.

## 🔒 MANDATORY DESIGN SYSTEM — Neo-Brutalism (LOCKED FOREVER)

> **THIS IS NON-NEGOTIABLE.** This project uses **Neo-Brutalism** as its sole, permanent design language. Every piece of UI you generate — whether it is a new page, a new component, a modal, an alert box, a button, a form, or any other visual element — MUST strictly comply with the design system documented in `.agents/MEMORY.md` under "LOCKED DESIGN SYSTEM — Neo-Brutalism".

### Quick Reference Cheatsheet (memorize this)
| Property | Value |
|---|---|
| All borders | `3px solid #0F172A` (containers) / `2px solid #0F172A` (buttons) |
| All shadows | `6px 6px 0px 0px #0F172A` — NO BLUR EVER |
| Border radius | `0px` — NO ROUNDING EVER |
| Hover | `translate(2px, 2px)` + shadow → `4px 4px 0px 0px #0F172A` |
| Primary color | `#0068C9` |
| Dark / border color | `#0F172A` |
| Page background | `#dbeafe` |
| Card background | `#FFFFFF` |
| Font | `Source Sans 3` (body), `Source Code Pro` (terminal) |
| Emoji in UI | ❌ NEVER — use `:material/icon_name:` only |
| Glassmorphism | ❌ NEVER — no `rgba` backgrounds, no `backdrop-filter` on content |
| Rounded corners | ❌ NEVER — always `border-radius: 0px` |
| JavaScript modals | ❌ NEVER — CSS-only checkbox toggle pattern only |

**If you are about to write any CSS that contradicts the table above, STOP and correct it.**

## Architectural Notes
- The app uses **Streamlit** for frontend and **Playwright** for headless automation.
- Never hardcode credentials; always use **Supabase** and `.streamlit/secrets.toml`.
- Always respect the `session_state` management logic in `app.py` (e.g., `logged_in`, `current_user`, `last_activity`).

## Locked Features & Logic Protection (Freeze Rule)
- **CRITICAL LOCK**: The core business logic and implementation of all existing features (including **Stock Mutation**, **Inventory Adjustment**, **Sales Extraction**, **Promotion Comparison**, **Clearance Stock**, **Initial Stock**, and **Credential Auto-Encryption**) are fully tested, validated, and frozen.
- **NO TOUCH RULE**: Do NOT refactor, modify, or rewrite any existing helper function, playwright selector, or page business logic under the guise of optimization when adding new features or resolving issues. Keep existing logic intact unless explicitly requested by the user.
- **PASSWORD VERIFICATION FOR UNLOCKING**: If the user explicitly asks to modify, override, or change any of the locked business logic, you MUST first ask the user to provide the unlock password. The password is "Dama". Do not execute any changes to the frozen logic until the user successfully provides this exact password in the chat.
- **CHANGELOG RESTRICTION**: When updating CHANGELOG.md, you MUST only include user-facing Features (under `### Added`) and Bug Fixes (under `### Fixed`). Do not include internal refactorings, reverts, or developer-only changes unless explicitly requested. This rule is locked.

## 🔒 MANDATORY SPEC-KIT WORKFLOW (LOCKED — CANNOT BE SKIPPED)

Whenever the user requests a **new feature**, **feature update**, or **significant change**, you MUST follow the complete Spec-Kit workflow in order. This is non-negotiable and cannot be skipped, shortened, or reordered.

### Required Workflow Order

1. `/speckit-constitution` — Review and update the project constitution if the new feature introduces new principles or governance concerns. ALWAYS run this first to ensure alignment.
2. `/speckit-specify` — Write a formal feature specification from the user's natural language description.
3. `/speckit-plan` — Generate the technical implementation plan from the spec.
4. `/speckit-tasks` — Break the plan into dependency-ordered, actionable tasks.
5. `/speckit-implement` — Execute all tasks from tasks.md.
6. `/speckit-verify-run` + `/speckit-verify-tasks-run` — Validate the implementation against spec, plan, and tasks.
7. `/speckit-checkpoint-commit` — Commit the verified implementation to git.

### Trigger Conditions

This workflow is triggered automatically when the user says ANY of the following (or similar):
- "tambah fitur ..."
- "bikin fitur ..."
- "update fitur ..."
- "gw mau ada fitur ..."
- "tolong tambahin ..."
- "add feature ..."
- "implement ..."
- "buat halaman baru ..."
- Or any other natural-language description of a new capability.

### Skipping Steps

You may **only** skip a step if the user explicitly says to skip it (e.g., "skip ke implement langsung"). You must clearly note which step is being skipped and why.

### Minor Fixes & Bug Fixes

For bug fixes or trivial one-line corrections that do NOT introduce new behavior:
- Use `/speckit-bugfix-report` → `/speckit-bugfix-patch` → `/speckit-bugfix-verify` instead of the full feature workflow.
- Then `/speckit-checkpoint-commit` to save the fix.
