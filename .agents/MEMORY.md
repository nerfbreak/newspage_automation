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
- **Avoid Glassmorphism/Translucency**: Do NOT use CSS properties like `backdrop-filter`, `rgba` on main containers, or complex gradients (glassmorphism) for the UI (including the login screen). It breaks Streamlit's layout rendering. Stick to solid, flat, modern colors (e.g., `#FFFFFF`, `#F8FAFC`).

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
- **2026-06-27**: Set the cat-with-laptop image (`static/favicon.png`) as the official global webpage favicon/icon for the Streamlit application in `app.py` page configuration.
- **2026-06-27**: Translated CHANGELOG.md to Indonesian (using "Fitur Baru" and "Perbaikan Bug" headers) and updated the dynamic parser in `app.py` to strip out metadata like `# Changelog` and `## [Unreleased]`, rendering only user-facing additions and fixes.
- **2026-06-27**: Rewrote CHANGELOG.md in a simple, jargon-free Indonesian format focusing strictly on user-facing features and feature improvements, removing technical developer terms like syntax errors, attribute errors, and file compilation details.
- **2026-06-27**: Reverted CHANGELOG.md back to English (using Added/Fixed headers), keeping it user-friendly and simple, and removed the auto-encryption and app icon entries per user request.
- **2026-06-27**: Implemented a comprehensive Operational Report & Analytics section on the main Dashboard page (0_dashboard.py). Added cached log fetching from Supabase, a period filter selector, KPI cards, interactive sync/extraction trend charts, and custom styled HTML tables showing recent execution logs under tabs.
- **2026-06-27**: Updated the footer disclaimer text in `utils.py` to be more professional, and explicitly stated that the application is unofficial and has no official affiliation with Reckitt, Accenture, or the Newspage platform.
- **2026-06-27**: Fixed HTML rendering bug in dashboard recent execution tables by wrapping them in `clean_html()`. Updated dashboard metric card and distributor chart to display count of unique SKUs adjusted instead of quantity volumes.
- **2026-06-27**: Replaced deprecated `use_container_width=True` with `width="stretch"` on dashboard charts to resolve Streamlit deprecation warnings.
- **2026-06-27**: Replaced deprecated `use_container_width=True` with `width="stretch"` on buttons across all locked pages (unlocked via "Dama" password verification) to resolve Streamlit deprecation warnings.
- **2026-06-27**: Simplified the Dashboard Activity Report: removed all charts (area chart, bar chart, status distribution) and separate tabbed tables. Replaced with a single unified "Execution History" table showing 5 columns: Timestamp, Distributor, Module (color-coded badges), Status, and Run By. Merges data from `adjustment_logs` and `extraction_history` tables. Module detection uses qty format to distinguish Inventory Adjustment vs Stock Mutation.
- **2026-06-27**: Fixed "Run By" column on Dashboard to show Streamlit login username instead of NP bot account code. Added optional `run_by` parameter to `log_adjustment()` in `database.py`. Updated `run_execution`, `run_execution_manual`, `run_mutasi_execution` in `playwright_engine.py` and all call sites in pages (1, 4, 5, 6) to pass `st.session_state.current_user`. Old log records without `run_by` fall back to showing `np_user`. Also requires adding a `run_by TEXT` column to the `adjustment_logs` table in Supabase (user action required).
- **2026-06-27**: Added "Today" option to dashboard period filter. Renamed "Execution History" header to "Log History".
- **2026-06-27**: Implemented File Upload Tracking on Dashboard. Added `log_uploaded_file()` to `database.py` storing base64-encoded Excel/CSV files in `uploaded_files` Supabase table. Updated `1_inventory_adjustment.py` to store the uploaded distributor file before execution (Auto Compare mode only). Dashboard `load_historical_logs()` now fetches `uploaded_files` and builds a 5-minute bucket lookup to match files to log rows. Log History table now has a 6th "File Uploaded" column rendering an inline base64 download anchor link. Requires user to create `uploaded_files` table in Supabase.