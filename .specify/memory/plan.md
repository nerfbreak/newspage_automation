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

## Testing Strategy

- Manual validation: Navigate all 7 page modules, verify no deprecation warnings, confirm layout integrity.
- Python syntax check: `python -c "import py_compile; py_compile.compile('filename.py')"` for all modified files.
- Responsive validation: Check 320px, 480px, and 768px viewports, including portrait/landscape behavior, button tap targets, and mobile stacked-card readability.
- Security Validation [Source: specs/018-security-audit]: Static code analysis on user input variables and dynamic command generation. Mock decryption payload with invalid keys to trigger graceful fails. Dependency scanning via `pip-audit`.

## Revision Notes

- **2026-07-06**: Archived `017-mobile-responsive` implementation details, responsive helper architecture, and mobile validation strategy.
- **2026-07-06**: Archived `018-security-audit` confirming secure configurations for sessions, inputs, and credentials.
