# Optimize Newspage Automation — Main Plan

**Last Updated**: 2026-07-06
**Revision**: Archived 017-mobile-responsive into main project memory

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: Streamlit, Playwright, Supabase
- **Storage**: Supabase (PostgreSQL)
- **Target Platform**: Windows / Streamlit Cloud
- **Project Type**: web-service
- **Constraints**: Neo-Brutalist design system (see constitution.md)

## Project Structure

```text
Optimize/
├── app.py                          # Main Streamlit entry point
├── playwright_engine.py            # Core Playwright automation engine
├── utils.py                        # Shared utility functions
├── pages/
│   ├── 0_dashboard.py              # Dashboard with KPIs and activity feed
│   ├── 1_inventory_adjustment.py   # Inventory adjustment module
│   ├── 2_sales_extraction.py       # Sales extraction module
│   ├── 3_promotion_comparison.py   # Promotion comparison module
│   ├── 4_stock_mutation.py         # Stock mutation module
│   ├── 5_clearance_stock.py        # Clearance stock module
│   └── 6_initial_stock.py          # Initial stock module
├── static/
│   └── style.css                   # Shared Neo-Brutalist CSS
├── specs/                          # Feature specifications
├── .specify/                       # Spec-Kit project memory
│   ├── memory/                     # Consolidated project memory
│   └── scripts/                    # Automation scripts
├── .agents/                        # Agent configuration
│   ├── MEMORY.md                   # Project memory & changelog
│   └── skills/                     # Spec-Kit workflow skills
├── .streamlit/
│   ├── config.toml                 # Streamlit configuration
│   └── secrets.toml                # Secret keys (gitignored)
└── requirements.txt                # Pinned dependencies
```

## Architecture Changes Log

### 016-replace-use-container-width (2026-07-05)
[Source: specs/016-replace-use-container-width]
- Migrated all 30 occurrences of deprecated `use_container_width=True` to `width='stretch'` across 9 Python files.
- No new dependencies, modules, or configuration changes introduced.
- No architectural changes — pure parameter replacement for Streamlit API compliance.

## Configuration

- All secrets in `.streamlit/secrets.toml` (gitignored)
- Supabase connection via `SUPABASE_URL` and `SUPABASE_KEY`
- `MASTER_KEY` for Fernet encryption of distributor credentials

## Recent Architecture Additions

### 017-mobile-responsive (2026-07-06)
[Source: specs/017-mobile-responsive]
- Added mobile-first responsive behavior using `@media (max-width: 768px)` rules in `static/style.css`.
- Added `utils.render_responsive_dataframe()` as the shared UI helper for desktop table and mobile stacked-card rendering.
- Updated data-heavy surfaces to route table previews/reports through responsive dataframe rendering while preserving frozen automation logic.
- No new dependencies, database schema changes, environment variables, routes, or Playwright selectors introduced.

### 018-security-audit (2026-07-06)
[Source: specs/018-security-audit]
- Integrated `pip-audit` for dependency vulnerability scanning.
- Validated AES-256 Fernet credential architecture against unauthorized keys, confirming exceptions are handled safely without data leaks.
- Confirmed input sanitization (XSS) via `html.escape()` and RCE prevention in subprocess invocations across all modules.
- Generated `audit_report.md` capturing the secure state of the application.

### 024-clear-sales-btn-color (2026-07-08)
[Source: specs/024-clear-sales-btn-color]
- Added `.red-btn-marker` CSS logic to apply specific Neo-Brutalism compliant red styling.
- Bound wrapper logic to Streamlit native element to differentiate the destructive "CLEAR DATA EXTRACTED SALES" button from primary action buttons.
- No new dependencies, modules, or database modifications introduced.

### 028-remove-force-kill (2026-07-09)
[Source: specs/028-remove-force-kill]
- Completely removed the "FORCE KILL" button and its underlying OS-level process termination logic (`psutil`) from `playwright_engine.py`.
- Reverted the changes introduced in Spec 025 to ensure the automation environment relies solely on standard "Terminate" procedures or system timeouts.
- Removed `psutil` dependency from the project.

### 027-replace-components-html (2026-07-10)
[Source: specs/027-replace-components-html]
- Replaced deprecated `st.components.v1.html` with `st.iframe` in `pages/1_inventory_adjustment.py` (screenshot share buttons).
- Removed the `import streamlit.components.v1 as components` statement.
- No new dependencies, database changes, or Playwright selector modifications introduced.
- Fulfills Constitution Principle X (Streamlit Deprecation Compliance).

### 029-neo-brutalist-section-headers (2026-07-10)
[Source: specs/029-neo-brutalist-section-headers]
- Replaced 7 instances of standard `st.subheader()` with custom HTML `<div class='header-wrapper-*'><span class='section-header-underline'>` across Stock Mutation, Clearance Stock, and Initial Stock pages.
- Added smoke test coverage `test_no_unsupported_subheaders_in_execution_pages` to prevent future drift.
- Fulfills Constitution Principle IV (Neo-Brutalism Design Language).

## Testing Strategy

- Manual validation: Navigate all 7 page modules, verify no deprecation warnings, confirm layout integrity.
- Python syntax check: `python -c "import py_compile; py_compile.compile('filename.py')"` for all modified files.
- Responsive validation: Check 320px, 480px, and 768px viewports, including portrait/landscape behavior, button tap targets, and mobile stacked-card readability.
- Security Validation [Source: specs/018-security-audit]: Static code analysis on user input variables and dynamic command generation. Mock decryption payload with invalid keys to trigger graceful fails. Dependency scanning via `pip-audit`.

## Revision Notes

- **2026-07-06**: Archived `017-mobile-responsive` implementation details, responsive helper architecture, and mobile validation strategy.
- **2026-07-06**: Archived `018-security-audit` confirming secure configurations for sessions, inputs, and credentials.
- **2026-07-09**: Archived `028-remove-force-kill` implementation details confirming the removal of `psutil` and the Force Kill feature.
- **2026-07-10**: Archived `027-replace-components-html` confirming migration from deprecated `st.components.v1.html` to `st.iframe`.
- **2026-07-10**: Archived `029-neo-brutalist-section-headers` standardizing all `st.subheader` calls to `.section-header-underline`.
