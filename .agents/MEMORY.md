# AI Project Memory (Optimize Newspage)

This file acts as the "Distributed Project Memory" for AI agents. It tracks architectural decisions, recent changes, and known states to prevent hallucinations and maintain a single source of truth across all AI sessions.

## Current State Summary
- **Frontend**: Streamlit (Pages: Dashboard, Inventory Adjustment, Sales Extraction, Promotion Comparison, Stock Mutation, Clearance Stock, Initial Stock).
- **Backend/DB**: Supabase (PostgreSQL) for user auth, vault, and system config. `cryptography` for AES-256 encryption.
- **Automation Engine**: Playwright (`playwright_engine.py`) handling interactions with the Newspage portal.
- **Selectors**: UI automation selectors are documented in `elements_yang_dipakai_dinewspage_sebagai_otomasi.md`.

## Preferred UI/UX & Design Guidelines
- **Clean Layout Spacing**: Always wrap section headers in `pages/` inside `.header-wrapper-center` or `.header-wrapper-left` container classes defined in `static/style.css` to prevent text sticking/cramping.
- **English-Translated Disclaimer Footer**: The footer disclaimer must remain in English, formatted with a soft blue background wrapper (`background-color: rgba(0, 104, 201, 0.04); border: 1px solid rgba(0, 104, 201, 0.1); border-radius: 8px`) for a clean, professional aesthetic.
- **Execution UI Visual Branding**: Replace generic or boring "Execution" subheaders with themed column titles. Use vertical colored borders on the left side of column headers to group actions (e.g., `#FF2B2B` red border for Deduct/Negative flow and `#09A53C` green border for Add/Positive flow).
- **Safe HTML & Character Rendering**: Never use raw HTML entity codes like `&nbsp;` directly in output logs that undergo `html.escape()`. Use regular space characters to prevent literal `&NBSP;` rendering bugs.

## Locked Features & Code Freeze
- **Frozen Modules**: **Stock Mutation**, **Inventory Adjustment**, **Sales Extraction**, **Promotion Comparison**, **Clearance Stock**, **Initial Stock**, and **Credential Auto-Encryption**.
- **Rule**: All core execution flow, Playwright steps, Supabase connections, and credential handling for these features are locked. Any future development or new features must build on top of or alongside these modules without modifying their verified core logics.
- **Unlock Password**: If modification to the frozen logic is explicitly requested, you must verify the password `"Dama"` in the chat before doing any changes.
- **Changelog Restriction**: When updating `CHANGELOG.md`, only user-facing Features (`### Added`) and Bug Fixes (`### Fixed`) must be recorded.



---

## Changelog & Decisions

- **2026-06-24**: Initialized AI Project Memory system. Established `AGENTS.md` to force all future AI interactions to read and write to this `MEMORY.md` file.
- **[Archived Decision]**: Implemented 5 login attempts lockout and 1-hour session timeout in `app.py`.
- **[Archived Decision]**: Implemented AES-256 Fernet encryption for `distributor_vault` credentials.
- **2026-06-24**: Reverted the Bento Box UI as it broke Streamlit's layout engine. Implemented a **Streamlit-Native Premium UI** instead: set elegant colors in `config.toml`, stripped destructive CSS overrides from `style.css` and `login.css`, and updated `utils.py` to use flat, safe, inline-styled HTML components.
- **2026-06-24**: Rolled back UI to original state per user request. Enabled global font antialiasing.
- **2026-06-25**: Critical security fixes — added `html.escape()` to all HTML injection points in `utils.py` (XSS prevention), enabled CORS in `config.toml`, pinned all dependency versions in `requirements.txt`, moved orphaned `refactor.py` to `scripts/`, added `EXCLUDE_PREFIX` constant to `database.py`, fixed misleading docstring in `database.py`, removed dead `style_status()` function from `utils.py`.
- **2026-06-26**: Fixed Stock Mutation quantity execution bug: added a fallback to the `Qty` column when `PAC`, `CAR`, and `EA` columns are missing, ensuring quantities are correctly written to the EA input in the Newspage portal instead of injecting empty/zero values. Pre-initialized Status and Keterangan columns in dataframes to avoid visual glitches.
- **2026-06-26**: Resolved "Decryption error" issue: restored missing local `.streamlit/secrets.toml` from backup to enable decryption of distributor passwords locally, and identified that `MASTER_KEY` needs to be set to `7Cm4lTUOm1-DPgwHRE28ZCZ28b33KDMVV_8Ug_AxiWM=` in the deployment env/secrets.
- **2026-06-26**: Implemented auto-encryption feature for plain-text passwords: if a distributor password stored in Supabase fails decryption and is detected as plain text (does not start with 'gAAAA'), it will be automatically encrypted and written back to Supabase on first fetch, enabling a seamless workflow for registering new distributors.
- **2026-06-27**: Documented design guidelines based on the user's positive feedback. The clean layout spacing, vertical left-bordered header highlights, soft-blue disclaimer wrapper, and escaped entity handling are established as the official UI/UX standard.
- **2026-06-27**: Resolved visual container collision on Page 4 (Stock Mutation) by extracting the execution block (dual tables, progress indicators, terminal logs, and success status indicators) outside the input `st.container(border=True)` block, letting them render naturally at the page level without cramped layout borders.
- **2026-06-27**: Established "Locked Features & Code Freeze" rule in both `AGENTS.md` and `MEMORY.md` per user request to freeze all existing core features and prevent future AI assistants from refactoring or modifying verified logic when adding new modules.
- **2026-06-27**: Added a Password Verification check ("Dama") to the logic freeze rules. Any request to override or modify locked modules must be verified by this password in the chat before execution.
- **2026-06-27**: Restricted CHANGELOG.md to only track user-facing Features (Added) and Bug Fixes (Fixed) per user's request. Added this restriction to local locked rules.
- **2026-06-27**: Fixed frozen progress bar issue in Stock Mutation by updating `run_execution_manual` to accept `progress_placeholder` and dynamically increment progress values, and passed `prog_a_ph`/`prog_b_ph` from `run_mutasi_execution` (Unlocked via password verification).
- **2026-06-27**: Consolidated the two separate success/error status boxes into a single merged status box on the Stock Mutation page to improve visual aesthetics and reduce clutter (Unlocked via password verification).
- **2026-06-27**: Updated the Streamlit login UI expander in `app.py` to dynamically load and display the contents of `CHANGELOG.md` instead of using a hardcoded text list, ensuring any future updates to `CHANGELOG.md` are instantly rendered in the app.