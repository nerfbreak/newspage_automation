# Error Taxonomy

**Project**: Optimize Newspage Automation  
**Last reviewed**: 2026-07-06  
**Status**: Documentation baseline and helper module only. No frozen automation flow has been rewired yet.

This document defines consistent error codes for user-facing UI messages, Telegram alerts, and operator logs. It addresses the security audit finding that raw exception strings can leak implementation details to users or chat notifications.

The helper module lives in `error_taxonomy.py`.

## Goals

- Give every recurring failure mode a stable code.
- Keep UI and Telegram messages safe and non-sensitive.
- Keep detailed exception text in server-side logs only.
- Make support triage faster by grouping errors by category and severity.
- Avoid behavioral changes to locked business logic until a specific migration task is approved.

## Code Format

Use this pattern:

```text
CATEGORY-NNN
```

Examples:

- `AUTH-001`: login failed.
- `CRED-002`: distributor credential could not be decrypted.
- `AUTO-002`: Newspage timeout or delayed response.

## Categories

| Prefix | Category | Typical owner |
|---|---|---|
| `AUTH` | Streamlit login and lockout | `app.py`, `database.py` |
| `SESSION` | session timeout and persistent cookie state | `app.py` |
| `CONFIG` | missing secrets or runtime configuration | `database.py`, page setup |
| `DB` | Supabase query/read/write failures | `database.py`, dashboard |
| `CRED` | distributor vault and encryption/decryption | `database.py` |
| `INPUT` | incomplete or invalid user input | page modules |
| `UPLOAD` | CSV/XLS/XLSX parsing and validation | page modules, `data_processor.py` |
| `AUTO` | Playwright/Newspage automation | `playwright_engine.py` |
| `NET` | external network requests | Supabase, Newspage, Telegram |
| `NOTIFY` | Telegram and proof screenshot notifications | `utils.py`, `playwright_engine.py` |
| `SEC` | policy guardrails and blocked risky operations | project rules |
| `UNK` | uncategorized fallback | any module |

## Baseline Codes

| Code | Severity | Safe user message | Operator hint |
|---|---|---|---|
| `AUTH-001` | warning | Login failed. Check the username and password. | Authentication failed for supplied Streamlit user. |
| `AUTH-002` | error | Account is temporarily locked after repeated failed login attempts. | Login lockout is active; verify whether attempts are legitimate. |
| `SESSION-001` | warning | Session expired. Please sign in again. | Session timeout or invalid persistent cookie. |
| `CONFIG-001` | critical | Application configuration is incomplete. | Check required Streamlit secrets or environment variables. |
| `DB-001` | error | Database request failed. Please retry or contact support. | Supabase query failed; inspect server logs for table and operation. |
| `CRED-001` | error | Distributor credential is not available. | Distributor vault row is missing or incomplete. |
| `CRED-002` | critical | Distributor credential could not be decrypted. | Verify `MASTER_KEY` and encrypted vault value. |
| `INPUT-001` | warning | Input is incomplete or invalid. | User-facing validation failed before execution. |
| `UPLOAD-001` | warning | Uploaded file could not be parsed. | Check extension, workbook structure, size, and required columns. |
| `AUTO-001` | error | Automation failed while opening or controlling the browser. | Playwright browser launch or install step failed. |
| `AUTO-002` | error | Newspage did not respond in time. | Portal timeout, ASP.NET postback delay, or unavailable page state. |
| `AUTO-003` | error | Automation could not find the expected Newspage element. | Selector or portal DOM changed; compare against element inventory. |
| `NET-001` | error | Network request failed. | External service, Newspage, Supabase, or Telegram request failed. |
| `NOTIFY-001` | warning | Notification could not be sent. | Telegram or screenshot delivery failed. |
| `SEC-001` | critical | Security guardrail blocked the operation. | Security policy, locked logic, or secret-handling rule blocked the action. |
| `UNK-001` | error | Unexpected error occurred. | Unhandled exception; inspect server logs with traceback. |

## Usage Pattern

For new or touched code, use safe text in UI/Telegram and detailed text in logs:

```python
import logging
from error_taxonomy import format_log_error, format_user_error

try:
    run_operation()
except TimeoutError as exc:
    logging.exception(format_log_error("AUTO-002", "Inventory extraction"))
    st.error(format_user_error("AUTO-002"))
```

Rules:

- Do not put raw `str(exc)` in `st.error()`, Telegram messages, downloadable files, or HTML.
- Use `logging.exception()` or `logging.error()` for detailed internal diagnostics.
- Add a new code to `error_taxonomy.py` and this document before introducing a new recurring error class.
- Prefer the most specific code available. Use `UNK-001` only as a temporary fallback.

## Migration Plan

1. Adopt the helper in non-frozen support paths first, such as dashboard loading and notification failures.
2. For frozen modules, only replace visible error strings during an approved bugfix or security-hardening task.
3. Keep existing business behavior intact: taxonomy should change presentation and triage, not execution decisions.
4. Add regression checklist rows when a visible error message changes.

**Status:**
- [x] Adopted in non-frozen support paths (`app.py`, `utils.py`, `pages/0_dashboard.py`) for login authentication, session timeouts, Telegram alert notifications, dashboard log loading, and superuser ping tests.
- [ ] Frozen business logic modules remain untouched per Freeze Rule (pending password unlock or bugfix tasks).

