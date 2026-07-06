# Security Audit Report

**Project**: Optimize Newspage Automation  
**Date**: 2026-07-06  
**Scope**: Read-only application security review for secrets, sessions, subprocess usage, HTML injection, uploads, logging, dependency surface, and Supabase evidence.  
**Mode**: No production actions, no frozen business logic edits, no secret values copied into this report.

## Executive Summary

The project already has several strong controls: bcrypt user passwords, Fernet-based credential encryption, login lockout, session timeout logic, gitignored local secrets, pinned dependencies, and broad use of `html.escape()` in shared UI helpers.

The main remaining risks are procedural/session hardening and auditability:

- Session cookies are encrypted but appear client-accessible and replayable for up to 7 days.
- The AI unlock password is stored in tracked project instructions, so it should be treated as a workflow guardrail, not a secret.
- Plain-text distributor passwords can still be accepted as a fallback during auto-encryption paths.
- File uploads have extension filters but no visible size/row/sheet limits.
- Many `unsafe_allow_html=True` surfaces exist; several dynamic values are escaped, but not all dynamic HTML paths are centrally enforced.
- Dependency CVE scanning was not completed because the available runtime did not have `pip-audit` installed and network access is restricted.

## Findings

| ID | Severity | Area | Evidence | Finding | Recommended Action |
|---|---|---|---|---|---|
| SEC-001 | High | Session cookie | `app.py:21-22`, `app.py:63-82` | `auth_user` is encrypted, but the cookie is managed client-side and no HttpOnly/Secure/SameSite controls are visible in app code. A stolen cookie may replay login for up to 7 days. | Shorten persistent session duration, add explicit cookie security attributes if supported, and consider server-side session validation or signed session IDs. |
| SEC-002 | High | Governance secret | `AGENTS.md:47` | The frozen-logic unlock password is stored in tracked instructions. This is useful as a procedural guardrail but should not be considered secret. | Move unlock approval to out-of-band user confirmation or rotate the unlock word after repo exposure. |
| SEC-003 | High | Credential encryption fallback | `database.py:145-157` | If vault password decryption fails and the value does not look encrypted, the app can use the plain-text value and attempt auto-encryption. If auto-encryption fails, it still falls back to the plain-text password for that run. | Treat plaintext vault credentials as a blocking security finding after migration; avoid plaintext fallback except in a controlled migration command. |
| SEC-004 | Medium | Local secrets hygiene | `.streamlit/secrets.toml`, `.gitignore:2`, `git ls-files` | Local secrets are present on disk and correctly ignored by git. They are not tracked, but this file contains live-looking runtime secrets. | Keep it local only, never paste contents into chat/issues/logs, and rotate secrets if the workspace is shared or backed up insecurely. |
| SEC-005 | Medium | HTML injection | `playwright_engine.py:728-734`, `pages/4_stock_mutation.py:189-204`, broad `unsafe_allow_html=True` scan | Shared helpers escape many values, but some dynamic HTML directly interpolates distributor/user values from Supabase/secrets/session without obvious escaping. This creates stored/reflected XSS risk if trusted data is polluted. | Introduce a strict convention: any dynamic value inside unsafe HTML must pass through `html.escape()` or a safe helper. Audit each direct f-string sink. |
| SEC-006 | Medium | File upload DoS / validation | `pages/1_inventory_adjustment.py:81`, `pages/1_inventory_adjustment.py:280-288`, `pages/3_promotion_comparison.py:53-78`, `pages/4_stock_mutation.py:70`, `pages/6_initial_stock.py:61-90`, `data_processor.py:11-31` | Uploads restrict extensions but no visible size, row count, sheet count, or cell volume caps are enforced before parsing CSV/XLSX. Large or crafted workbooks could exhaust memory or slow the app. | Add shared upload validation for size, extension, row/cell limits, and friendly rejection before parsing. |
| SEC-007 | Medium | Dependency CVE coverage | `requirements.txt`; attempted `python -m pip_audit --version` | Dependencies are pinned, but the dependency list is very large and no CVE scan could be run in this environment because `pip-audit` was unavailable. | Run `pip-audit -r requirements.txt` or an equivalent scanner in a network-enabled environment and save the result. |
| SEC-008 | Medium | Supabase RLS / migration evidence | `README.md`, `product_requirements_document.md`, `database.py` | The constitution requires RLS, but the repo does not show migration SQL or policy docs for tables like `users_auth`, `distributor_vault`, `adjustment_logs`, `extraction_history`, or `uploaded_files`. | Create `docs/database_migrations.md` or SQL migration files documenting tables, RLS status, and policies. |
| SEC-009 | Low | Subprocess execution | `pages/0_dashboard.py:305-354`, `playwright_engine.py:77-80` | Subprocess calls use argument lists and pass ping credentials via environment variables rather than formatting them into the command string. This is good. The remaining risk is embedded Python script complexity and dependency installation from runtime. | Keep subprocess inputs environment-based; consider moving the ping script into a checked-in helper module for reviewability. |
| SEC-010 | Low | Sensitive screenshots and alerts | `playwright_engine.py:47-51`, `playwright_engine.py:654-714`, `utils.py:51-71`, `pages/1_inventory_adjustment.py:420-583` | Screenshots are gitignored and Telegram deletion is attempted after send. Screenshots can still contain sensitive portal data and may remain locally for failed/non-Telegram sharing flows. | Add retention rules and a cleanup command for old screenshots; avoid sending screenshots to group chats unless necessary. |
| SEC-011 | Low | Error detail exposure | `playwright_engine.py:376-378`, `playwright_engine.py:575-578`, `playwright_engine.py:1063-1066`, `database.py:116`, `database.py:161` | Some UI/Telegram errors include exception strings. These are useful for operations but can expose implementation details. | Categorize errors with safe user-facing codes and keep detailed traces server-side only. |

## Positive Controls Observed

- `.streamlit/secrets.toml` and `.env` are ignored by git.
- User passwords are checked with bcrypt in `database.authenticate_user()`.
- `MASTER_KEY` is loaded from Streamlit secrets or environment, not from app source.
- Login lockout exists with 5 attempts and 5-minute lockout defaults.
- Session timeout logic exists in `app.py`.
- Most high-volume dataframe/mobile rendering uses escaped values in `utils.render_responsive_dataframe()`.
- Subprocess calls observed use argument lists instead of `shell=True`.
- Screenshot directory is gitignored.

## Dependency CVE Status

Completed on 2026-07-07 using `pip-audit` in pinned/no-dependency-resolution mode because the full resolver timed out on the large requirements set.

Command:

```powershell
python -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off
```

Findings remediated by bumping pinned versions in `requirements.txt`:

- `langchain` 1.3.1 -> 1.3.9
- `langgraph-checkpoint` 4.1.0 -> 4.1.1
- `langgraph-sdk` 0.3.14 -> 0.3.15
- `langsmith` 0.8.5 -> 0.8.18
- `msgpack` 1.1.2 -> 1.2.1
- `pypdf` 6.11.0 -> 6.13.3

Remaining documented exception:

- `torch` 2.12.0 / `CVE-2025-3000`: `pip-audit` reported no fix version. The CI dependency audit ignores only this specific CVE while the project owner decides whether to remove Torch-dependent packages or move to a later safe Torch release when one is available.

## Suggested Follow-Up Order

1. Run dependency CVE scan and attach results.
2. Decide whether to harden session cookie handling or reduce cookie lifetime.
3. Replace plaintext credential fallback with an explicit migration-only path.
4. Add shared upload validation before CSV/XLSX parsing.
5. Centralize safe HTML rendering rules for all dynamic unsafe HTML.
6. Create database migration/RLS documentation.
7. Add error code taxonomy for user-facing and Telegram errors.

## Out of Scope

- No live Supabase RLS inspection was performed.
- No Newspage portal penetration testing was performed.
- No secrets were rotated.
- No business logic or Playwright selector behavior was modified.
