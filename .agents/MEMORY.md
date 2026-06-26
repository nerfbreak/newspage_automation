# AI Project Memory (Optimize Newspage)

This file acts as the "Distributed Project Memory" for AI agents. It tracks architectural decisions, recent changes, and known states to prevent hallucinations and maintain a single source of truth across all AI sessions.

## Current State Summary
- **Frontend**: Streamlit (Pages: Dashboard, Inventory Adjustment, Sales Extraction, Promotion Comparison, Stock Mutation, Clearance Stock, Initial Stock).
- **Backend/DB**: Supabase (PostgreSQL) for user auth, vault, and system config. `cryptography` for AES-256 encryption.
- **Automation Engine**: Playwright (`playwright_engine.py`) handling interactions with the Newspage portal.
- **Selectors**: UI automation selectors are documented in `elements_yang_dipakai_dinewspage_sebagai_otomasi.md`.

## AI Rules
- Read this file before proposing large changes.
- Update the "Changelog & Decisions" section below whenever you complete a task.

---

## Changelog & Decisions

- **2026-06-24**: Initialized AI Project Memory system. Established `AGENTS.md` to force all future AI interactions to read and write to this `MEMORY.md` file.
- **[Archived Decision]**: Implemented 5 login attempts lockout and 1-hour session timeout in `app.py`.
- **[Archived Decision]**: Implemented AES-256 Fernet encryption for `distributor_vault` credentials.
- **2026-06-24**: Reverted the Bento Box UI as it broke Streamlit's layout engine. Implemented a **Streamlit-Native Premium UI** instead: set elegant colors in `config.toml`, stripped destructive CSS overrides from `style.css` and `login.css`, and updated `utils.py` to use flat, safe, inline-styled HTML components.
- **2026-06-24**: Rolled back UI to original state per user request. Enabled global font antialiasing.
- **2026-06-25**: Critical security fixes — added `html.escape()` to all HTML injection points in `utils.py` (XSS prevention), enabled CORS in `config.toml`, pinned all dependency versions in `requirements.txt`, moved orphaned `refactor.py` to `scripts/`, added `EXCLUDE_PREFIX` constant to `database.py`, fixed misleading docstring in `database.py`, removed dead `style_status()` function from `utils.py`.
- **2026-06-26**: Fixed Stock Mutation quantity execution bug: added a fallback to the `Qty` column when `PAC`, `CAR`, and `EA` columns are missing, ensuring quantities are correctly written to the EA input in the Newspage portal instead of injecting empty/zero values. Pre-initialized Status and Keterangan columns in dataframes to avoid visual glitches.