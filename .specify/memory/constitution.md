<!--
SYNC IMPACT REPORT
==================
Version change: 2.5.0 → 2.6.0 (Added Principle XII: Minimal & Clean Dependency Architecture)
Added sections: Core Principles -> XII. Minimal & Clean Dependency Architecture (No Unused Bloat)
Modified sections: Governance (Version bump to 2.6.0, Last Amended: 2026-07-07)
Removed sections: None
Templates requiring updates:
  ✅ .specify/memory/constitution.md (Updated)
  ✅ requirements.txt (Pruning unused deployment bloat like litellm to fix Python version incompatibility)
Follow-up TODOs: None.
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

### II. Security-First Credential Handling & Session Protection
- **Credential Encryption**: Credentials MUST never be hardcoded in source files. All distributor passwords MUST be stored in Supabase and encrypted with AES-256 (Fernet). The master encryption key MUST reside exclusively in `.streamlit/secrets.toml` (local) or Streamlit Cloud environment secrets (deployment). Auto-encryption of plain-text passwords on first fetch is permitted and encouraged.
- **Session Integrity**: Plaintext identifiers (such as raw usernames) MUST NOT be stored in browser cookies for session validation without digital signatures (HMAC) or encryption. Cookies used for auto-login/session-persistence must be signed or encrypted using the `MASTER_KEY` to prevent privilege escalation and account spoofing.
- **Execution Sanitization**: Subprocess invocations (like Playwright test scripts) MUST NOT format user inputs or database config strings directly into python script text/commands. All dynamic inputs MUST be passed safely via operating system environment variables or standard input (stdin) to prevent Command/Code Injection (RCE).
- **Least Privilege & RLS**: PostgreSQL Row-Level Security (RLS) MUST be enabled on Supabase tables to prevent unauthorized read/write access. Database client keys MUST restrict table queries to the absolute minimum required.

**Rationale**: The application handles sensitive distributor credentials and execution configurations. A session hijack or code injection would allow unauthorized access or complete server compromise, affecting business operations and financial logs.

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

### VI. Free & Serverless External Integrations
All new external integrations or messaging bridges (e.g., forwarding Telegram screenshots to WhatsApp) MUST prioritize zero-cost, fully free deployment architectures. If a separate project or web service is required for the integration, it MUST be hosted on platforms providing adequate free tiers without incurring ongoing costs. For heavy workloads like WhatsApp engines, self-hosted API Gateways (e.g., `rmyndharis/OpenWA`) deployed via Docker on free platforms like Hugging Face Spaces are preferred over heavy monolithic scripts.

**Rationale**: To maintain the project's low-overhead operating model, auxiliary features like notification forwarding should not introduce new monthly server expenses. Separating the heavy engine from the lightweight logic (relay) ensures better stability and resource utilization.

### VII. Action Button Consolidation
To prevent UI clutter and maintain a clean interface, post-execution actions (e.g., "Clear Data") MUST dynamically replace the primary execution button (e.g., "Extract") in the exact same layout location once a task completes successfully. Secondary action buttons MUST NOT stack or multiply endlessly below the main containers.

**Rationale**: A clean, uncluttered interface is crucial for non-technical users. Stacking multiple action buttons creates confusion about the current state of the application. Reusing the primary button slot for state-dependent actions clarifies the available next steps and reduces visual noise.

### VIII. Mandatory Remark Input for Adjustments
Before executing the Inventory Adjustment module, there MUST be a "Remark" input column provided to the user, formatted exactly like the one present in the Stock Mutation module. If the user uploads a data file (e.g., CSV/Excel) to populate the grid, this Remark column MUST be automatically pre-filled with the base name of the uploaded file (explicitly excluding file extensions such as .xlsx, .csv, .xls, etc.) to reduce manual entry effort, while remaining fully editable. The adjustment process MUST NOT proceed if this step is bypassed.

**Rationale**: Ensures traceability and accountability for inventory adjustments by forcing operators to provide a contextual reason or reference note before data is submitted to the system, while automating repetitive tasks like copy-pasting filenames.

### IX. Client-Side Sharing Delegation
When integrating with third-party messaging services (e.g., sharing screenshots to WhatsApp), the system MUST prioritize browser-native delegation (such as Clipboard API copy followed by user-triggered window redirect) over backend headless bots. This ensures the action executes under the user's local browser session, eliminates server-side credentials/session management, and respects user privacy.

**Rationale**: Since users already maintain active, authenticated WhatsApp sessions on their personal local web browsers/laptops, utilizing browser-native capabilities (copy-pasting and opening WhatsApp Web) avoids the resource overhead, maintenance burden, and security risks associated with managing server-side headless browser sessions or storing third-party authentication tokens.

### X. Streamlit Deprecation Compliance — Layout Widths
All Streamlit widget and layout container calls MUST use the `width` parameter instead of the deprecated `use_container_width` parameter (which will be removed after 2025-12-31).
- For `use_container_width=True`, replace with `width='stretch'`.
- For `use_container_width=False`, replace with `width='content'`.

**Rationale**: Adhering to the updated Streamlit layout APIs avoids runtime crashes and deprecation warnings, ensuring long-term application stability and grid-layout compatibility.

### XI. Mobile-First Responsive Design
All new features, UI components, and pages MUST be designed with dynamic responsiveness, specifically optimizing for mobile viewports. Layouts must be precise and ensure that UI elements (buttons, tables, forms, containers) do not overlap, clip, or stack incorrectly when viewed on smaller screens. The responsive design MUST still strictly adhere to the locked Neo-Brutalism design system (e.g., maintaining exact borders, colors, and shadows).

**Rationale**: Users often access the application via mobile devices in on-the-go scenarios. Non-responsive UI elements that overlap or overflow the screen bounds create a frustrating user experience and prevent successful task execution.

### XII. Minimal & Clean Dependency Architecture (No Unused Bloat)
All packages listed in `requirements.txt` MUST be directly required by the application's runtime imports (e.g., Streamlit, Playwright, Supabase, Pandas, Cryptography, Requests) or their direct transitive dependencies. Unused heavyweight AI/ML frameworks, agent SDKs, or external API libraries (such as `litellm`, `mcp`, `fastapi`, `google-cloud-*`, `huggingface_hub`, `lark-oapi`) MUST NOT be included in production deployment requirements.

**Rationale**: Including unused packages bloating the dependency tree causes Python runtime version conflicts (such as `litellm==1.86.2` requiring Python >=3.10 while deployment environments like Streamlit Cloud may run Python 3.9), inflates build and startup times, and unnecessarily expands the CVE vulnerability attack surface.

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

**Version**: 2.6.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-07-07
