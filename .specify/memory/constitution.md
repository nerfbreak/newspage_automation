<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Added sections:
  - Core Principles (5 principles)
  - Security & Credential Standards
  - Development Workflow & Code Freeze
  - Governance
Templates requiring updates:
  ✅ .specify/memory/constitution.md (this file — written now)
  ✅ Aligned with .agents/MEMORY.md and .agents/AGENTS.md constraints
Follow-up TODOs: None — all placeholders resolved.
-->

# Optimize Newspage Automation Constitution

## Core Principles

### I. Feature Freeze — Verified Logic Is Sacred
All core features that have been tested and validated in production MUST NOT be
refactored, rewritten, or structurally modified without explicit user authorization.
This covers: Stock Mutation, Inventory Adjustment, Sales Extraction, Promotion
Comparison, Clearance Stock, Initial Stock, and Credential Auto-Encryption.

**Rationale**: These modules interact with a live production portal (Newspage/Accenture).
Untested changes risk data corruption, failed automation runs, and financial reporting
errors. Stability is more valuable than code elegance.

**Unlock procedure**: Any request to modify frozen logic MUST be verified by the
unlock password `"Dama"` in the active chat session before any changes are executed.

### II. Security-First Credential Handling
Credentials MUST never be hardcoded in source files. All distributor passwords MUST
be stored in Supabase and encrypted with AES-256 (Fernet). The master encryption key
MUST reside exclusively in `.streamlit/secrets.toml` (local) or Streamlit Cloud
environment secrets (deployment). Auto-encryption of plain-text passwords on first
fetch is permitted and encouraged.

**Rationale**: The application handles login credentials for multiple distributors.
A leak would allow unauthorized portal access affecting inventory and sales data
across the entire distribution network.

### III. Selector Integrity — No Guessing Allowed
Playwright selectors used for browser automation MUST be sourced from
`elements_yang_dipakai_dinewspage_sebagai_otomasi.md`. Do NOT invent, guess, or
derive selectors from memory. If a selector is missing, it MUST be discovered via
the Element Crawler (Page 7) before implementation.

**Rationale**: The Newspage portal is a third-party system not under our control.
Wrong selectors cause silent failures — the automation completes without error but
writes incorrect data to the system.

### IV. UI Consistency — Flat & Premium Design
All UI additions MUST follow the established design system:
- Background: solid `#FFFFFF` — no glassmorphism, no `backdrop-filter`, no textures.
- Streamlit native header and sidebar MUST remain hidden (`display: none !important`).
- Main container MUST retain the blue top border (`border-top: 4px solid #0068C9`).
- Section headers use the `.section-header-underline` pattern (full-width block).
- Execution columns use vertical color borders: `#FF2B2B` for deduct, `#09A53C` for add.
- Footer disclaimer MUST remain in English with the soft-blue wrapper styling.
- All shared CSS MUST live in `static/style.css` — no inline `<style>` blocks in pages.

**Rationale**: A fragmented design creates a perception of an unstable, untrustworthy
tool. Consistency signals professionalism to end-users who are non-technical operations
staff at distributor locations.

### V. Session & Logging Integrity
Every automation execution MUST be logged to Supabase with: timestamp, distributor,
module name, status, and the `current_user` (Streamlit login username). Session state
MUST track `logged_in`, `current_user`, and `last_activity`. Sessions expire after
1 hour of inactivity (5 failed login attempts trigger lockout).

**Rationale**: The Dashboard's activity feed and KPI metrics depend entirely on
consistent, structured log data. Gaps in logging corrupt analytics and make it
impossible to audit which user ran which operation.

## Security & Credential Standards

- All secrets MUST be stored in `.streamlit/secrets.toml` — this file is gitignored.
- The `distributor_vault` table in Supabase stores only encrypted credentials.
- `MASTER_KEY` in deployment environment MUST be set before any distributor credential
  fetch can succeed.
- HTML output in logs and UI MUST be escaped with `html.escape()` to prevent XSS.
- CORS is enabled in `config.toml`. Do not disable it.
- All dependency versions in `requirements.txt` MUST be pinned (no `>=` ranges).

## Development Workflow & Code Freeze

**Adding new features**:
1. Read `.agents/MEMORY.md` before starting any session.
2. New features MUST be implemented as new page files under `pages/` or new helper
   functions — never by modifying existing frozen modules.
3. New Playwright selectors MUST be verified via the Element Crawler before use.
4. After completing a task, append a changelog entry to `.agents/MEMORY.md`.

**Modifying frozen modules**:
1. User MUST provide the password `"Dama"` in the active session.
2. Changes MUST be minimal and surgical — touch only what is necessary.
3. Log the change in `.agents/MEMORY.md` with `(Unlocked via password verification)`.

**CHANGELOG.md rules**:
- Only user-facing entries are permitted: `### Added` (new features) and
  `### Fixed` (bug fixes visible to end-users).
- Do NOT log internal refactors, reverts, or developer-only changes.

## Governance

This constitution supersedes all conflicting instructions in any individual session.
It is enforced by the rules in `.agents/AGENTS.md` and referenced by `.agents/MEMORY.md`.

Amendments require:
1. A clear rationale documented in the active session.
2. A version bump following semantic versioning:
   - **MAJOR**: Removal or fundamental redefinition of a principle.
   - **MINOR**: New principle or section added.
   - **PATCH**: Wording clarifications, typo fixes.
3. Update of `LAST_AMENDED_DATE` and `CONSTITUTION_VERSION` in this file.
4. Append a note to `.agents/MEMORY.md` under "Changelog & Decisions".

All AI coding agents working on this project MUST read this constitution at the
start of each session alongside `.agents/MEMORY.md`.

**Version**: 1.0.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-06-30
