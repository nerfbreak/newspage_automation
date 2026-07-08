<!--
SYNC IMPACT REPORT
==================
Version change: 2.6.0 -> 2.7.0 (Aligned Principle IV with locked Neo-Brutalism)
Added sections: None
Modified sections:
  - Principle IV: UI Consistency - Flat & Premium Design -> UI Consistency - Locked Neo-Brutalism
  - Governance (Version bump to 2.7.0, Last Amended: 2026-07-08)
Removed sections: None
Templates requiring updates:
  - .specify/memory/constitution.md: updated
  - .specify/templates/plan-template.md: reviewed; generic Constitution Check remains aligned
  - .specify/templates/spec-template.md: reviewed; no mandatory section changes required
  - .specify/templates/tasks-template.md: reviewed; no task category changes required
  - .specify/templates/commands/*.md: not present in this checkout; no action needed
  - README.md and docs/quickstart.md: reviewed; no constitution-specific updates required
Follow-up TODOs: None.
-->

# Optimize Newspage Automation Constitution

## Core Principles

### I. Feature Freeze - Verified Logic Is Sacred
All core features that have been tested and validated in production MUST NOT be
refactored, rewritten, or structurally modified without explicit user authorization.
This covers: Stock Mutation, Inventory Adjustment, Sales Extraction, Promotion
Comparison, Clearance Stock, Initial Stock, and Credential Auto-Encryption.

**Rationale**: These modules interact with a live production portal (Newspage/Accenture).
Untested changes risk data corruption, failed automation runs, and financial reporting
errors. Stability is more valuable than code elegance.

**Unlock procedure**: Any request to modify frozen logic MUST be verified by the
unlock password `"Dama"` in the active chat session before any changes are executed.

### II. Security-First Credential Handling & Session Protection
- **Credential Encryption**: Credentials MUST never be hardcoded in source files.
  All distributor passwords MUST be stored in Supabase and encrypted with AES-256
  (Fernet). The master encryption key MUST reside exclusively in
  `.streamlit/secrets.toml` (local) or Streamlit Cloud environment secrets
  (deployment). Auto-encryption of plain-text passwords on first fetch is permitted.
- **Session Integrity**: Plaintext identifiers such as raw usernames MUST NOT be
  stored in browser cookies for session validation without digital signatures or
  encryption. Cookies used for auto-login or session persistence MUST be signed or
  encrypted using the `MASTER_KEY` to prevent privilege escalation and spoofing.
- **Execution Sanitization**: Subprocess invocations MUST NOT format user inputs or
  database config strings directly into script text or commands. Dynamic inputs MUST
  be passed safely via environment variables, structured arguments, or stdin.
- **Least Privilege & RLS**: PostgreSQL Row-Level Security (RLS) MUST be enabled on
  Supabase tables. Database client keys MUST restrict table queries to the minimum
  required access.

**Rationale**: The application handles sensitive distributor credentials and execution
configuration. A session hijack or code injection could compromise business operations
and financial logs.

### III. Selector Integrity - No Guessing Allowed
Playwright selectors used for browser automation MUST be sourced from
`elements_yang_dipakai_dinewspage_sebagai_otomasi.md`. Do NOT invent, guess, or
derive selectors from memory. If a selector is missing, it MUST be discovered via
the Element Crawler (Page 7) before implementation.

**Rationale**: The Newspage portal is a third-party system not under our control.
Wrong selectors can cause silent failures where automation completes but writes
incorrect data to the system.

### IV. UI Consistency - Locked Neo-Brutalism
All UI additions and edits MUST follow the locked Neo-Brutalism design system:
- Page background MUST be `#dbeafe`; card and container backgrounds MUST be `#FFFFFF`.
- Containers/cards MUST use `3px solid #0F172A`, `6px 6px 0px 0px #0F172A`,
  and `border-radius: 0px`.
- Buttons MUST use `2px solid #0F172A`, flat no-blur shadows, and the established
  pressed hover/active movement.
- UI elements MUST NOT use rounded corners, glassmorphism, blurred shadows, or emoji.
- Streamlit native header and sidebar MUST remain hidden (`display: none !important`).
- Shared styling SHOULD live in `static/style.css`; any scoped inline CSS MUST preserve
  the exact locked tokens and MUST NOT create a competing design language.
- Dynamic user-facing HTML MUST be escaped before rendering.

**Rationale**: A fragmented design creates a perception of an unstable, untrustworthy
tool. Consistency signals professionalism to non-technical operations users.

### V. Session & Logging Integrity
Every automation execution MUST be logged to Supabase with timestamp, distributor,
module name, status, and the `current_user` (Streamlit login username). Session state
MUST track `logged_in`, `current_user`, and `last_activity`. Sessions expire after
1 hour of inactivity, and 5 failed login attempts trigger lockout.

**Rationale**: The Dashboard activity feed and KPI metrics depend on consistent,
structured log data. Gaps in logging corrupt analytics and prevent auditability.

### VI. Free & Serverless External Integrations
All new external integrations or messaging bridges MUST prioritize zero-cost, free
deployment architectures. If a separate project or web service is required, it MUST be
hosted on a platform with an adequate free tier. Heavy workloads such as WhatsApp
engines SHOULD be isolated from lightweight relay logic.

**Rationale**: Auxiliary features must not introduce monthly server expenses or
unnecessary operational burden.

### VII. Action Button Consolidation
Post-execution actions such as "Clear Data" MUST dynamically replace the primary
execution button in the same layout location once a task completes successfully.
Secondary action buttons MUST NOT stack or multiply endlessly below main containers.

**Rationale**: Reusing the primary button slot clarifies the current available action
and reduces visual noise for non-technical users.

### VIII. Mandatory Remark Input for Adjustments
Before executing the Inventory Adjustment module, there MUST be a "Remark" input
column formatted like the one present in the Stock Mutation module. If the user uploads
a data file to populate the grid, this Remark column MUST be automatically pre-filled
with the uploaded file base name, excluding extensions such as `.xlsx`, `.csv`, and
`.xls`, while remaining fully editable. Adjustment execution MUST NOT proceed if this
step is bypassed.

**Rationale**: Mandatory remarks ensure traceability and accountability for inventory
adjustments while reducing repetitive manual entry.

### IX. Client-Side Sharing Delegation
When integrating with third-party messaging services, the system MUST prioritize
browser-native delegation, such as Clipboard API copy followed by a user-triggered
window redirect, over backend headless bots.

**Rationale**: Users already maintain authenticated messaging sessions locally. Browser
delegation avoids server-side credential management and protects user privacy.

### X. Streamlit Deprecation Compliance - Layout Widths
All Streamlit widget and layout container calls MUST use the `width` parameter instead
of the deprecated `use_container_width` parameter, which will be removed after
2025-12-31.
- For `use_container_width=True`, replace with `width='stretch'`.
- For `use_container_width=False`, replace with `width='content'`.

**Rationale**: Adhering to updated Streamlit layout APIs avoids runtime crashes and
deprecation warnings.

### XI. Mobile-First Responsive Design
All new features, UI components, and pages MUST be designed with dynamic responsiveness
for mobile viewports. Layouts MUST prevent overlap, clipping, and broken stacking on
smaller screens while preserving the locked Neo-Brutalism design system.

**Rationale**: Users often access the application on mobile devices while working.
Non-responsive UI prevents successful task execution.

### XII. Minimal & Clean Dependency Architecture (No Unused Bloat)
All packages listed in `requirements.txt` MUST be directly required by application
runtime imports or their direct transitive dependencies. Unused heavyweight AI/ML
frameworks, agent SDKs, OS-specific packages, or external API libraries MUST NOT be
included in production deployment requirements.

**Rationale**: Unused dependency bloat causes runtime version conflicts, increases
build time, and expands the CVE attack surface.

## Security & Credential Standards

- All secrets MUST be stored in `.streamlit/secrets.toml` or deployment secrets; local
  secrets files MUST remain gitignored.
- The `distributor_vault` table in Supabase stores only encrypted credentials.
- `MASTER_KEY` in deployment environment MUST be set before distributor credential
  fetches can succeed.
- HTML output in logs and UI MUST be escaped with `html.escape()` to prevent XSS.
- CORS is enabled in `config.toml`. Do not disable it.
- All dependency versions in `requirements.txt` MUST be pinned.

## Development Workflow & Code Freeze

**Adding new features**:
1. Read `.agents/MEMORY.md` before starting any session.
2. New features MUST be implemented as new page files under `pages/` or new helper
   functions whenever possible, and MUST NOT modify frozen execution logic.
3. New Playwright selectors MUST be verified via the Element Crawler before use.
4. After completing a task, append a changelog entry to `.agents/MEMORY.md`.

**Modifying frozen modules**:
1. User MUST provide the password `"Dama"` in the active session.
2. Changes MUST be minimal and surgical, touching only what is necessary.
3. Log the change in `.agents/MEMORY.md` with `(Unlocked via password verification)`.

**CHANGELOG.md rules**:
- Only user-facing entries are permitted: `### Added` for new features and
  `### Fixed` for bug fixes visible to end users.
- Do NOT log internal refactors, reverts, or developer-only changes.

## Governance

This constitution supersedes all conflicting instructions in any individual session.
It is enforced by the rules in `AGENTS.md` and referenced by `.agents/MEMORY.md`.

Amendments require:
1. A clear rationale documented in the active session.
2. A version bump following semantic versioning:
   - **MAJOR**: Removal or fundamental redefinition of a principle.
   - **MINOR**: New principle, materially expanded principle, or material governance
     alignment with locked project rules.
   - **PATCH**: Wording clarifications, typo fixes, and non-semantic refinements.
3. Update of `LAST_AMENDED_DATE` and `CONSTITUTION_VERSION` in this file.
4. Append a note to `.agents/MEMORY.md` under "Changelog & Decisions".

All AI coding agents working on this project MUST read this constitution at the start
of each session alongside `.agents/MEMORY.md`.

**Version**: 2.7.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-07-08
