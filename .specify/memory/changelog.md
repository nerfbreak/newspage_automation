# Optimize Newspage Automation — Merged Features Log

## Merged Features Log

### Streamlit Layout Width Deprecation Migration — 2026-07-05
**Branch:** `016-replace-use-container-width`
**Spec:** specs/016-replace-use-container-width

**What was added:**
- Migrated all deprecated `use_container_width` parameter usages to the modern `width` parameter across the entire codebase
- `use_container_width=True` → `width='stretch'` (30 occurrences in 9 files)
- Ensures compliance with Streamlit API deprecation (removal after 2025-12-31)
- Ratified Constitution Principle X to formalize this migration rule

**New Components:**
- None — pure parameter replacement, no new modules or services

**Tasks Completed:** 12/12 tasks

### Mobile-First Responsive Design - 2026-07-06
**Branch:** `017-mobile-responsive`
**Spec:** specs/017-mobile-responsive

**What was added:**
- Added mobile-first responsive layout behavior for Streamlit pages under 768px viewport width
- Added stacked mobile card rendering for wide dataframe/report views
- Preserved the locked Neo-Brutalism design system across responsive containers, buttons, and data cards
- Confirmed deprecated `use_container_width` remains disallowed in favor of Streamlit `width` parameters

**New Components:**
- `utils.render_responsive_dataframe()` shared responsive dataframe/table helper
- Mobile-specific CSS classes and media queries in `static/style.css`

**Tasks Completed:** 12/12 tasks

**Revision note:** Archived on 2026-07-06 from `specs/017-mobile-responsive`.

### System Security Audit - 2026-07-06
**Branch:** `018-security-audit`
**Spec:** specs/018-security-audit

**What was added:**
- Validated application security against the project's strict Security-First constitution
- Scanned Python dependencies using `pip-audit` to ensure zero vulnerable packages (CVEs)
- Verified AES-256 Fernet credential decryption robustness by injecting invalid mock keys (verified safe `InvalidToken` rejection)
- Conducted static code analysis on `utils.py` and `0_dashboard.py` confirming complete XSS (via `html.escape()`) and RCE mitigation

**New Components:**
- None — audit validated existing components and generated `audit_report.md`

**Tasks Completed:** 14/14 tasks

### Clear Sales Button Color - 2026-07-08
**Branch:** `024-clear-sales-btn-color`
**Spec:** specs/024-clear-sales-btn-color

**What was added:**
- Styled the "Clear Data Extracted Sales" button with a red color to visually signify its destructive action.
- Ensured full adherence to the global Neo-Brutalism design rules (hard borders, solid shadows, sharp edges).

**New Components:**
- None — modified `static/style.css` and injected a wrapping marker in the Streamlit page layout.

**Tasks Completed:** 4/4 tasks
