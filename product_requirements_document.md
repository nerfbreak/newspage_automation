# Product Requirements Document: Optimize Newspage Automation

## 1. Overview

Optimize Newspage Automation is a Streamlit-based internal operations tool for automating repetitive Newspage portal workflows. The product helps users extract stock and sales data, compare distributor data against Newspage records, execute stock adjustments, run stock mutation workflows, and monitor execution history from a single dashboard.

The application is designed for operational accuracy, controlled automation, and fast repeated use by business users who work with distributor inventory and sales data.

## 2. Product Goals

- Reduce manual work in Newspage inventory, sales, and promotion workflows.
- Improve accuracy when comparing distributor stock against Newspage stock.
- Provide repeatable, auditable automation runs with clear execution logs.
- Keep sensitive credentials out of source code and local UI inputs.
- Preserve the locked Neo-Brutalism UI design system across all screens.
- Protect verified automation flows from accidental refactors or behavioral drift.

## 3. Target Users

- Operations users who run stock adjustment, extraction, and reconciliation tasks.
- Inventory controllers who review stock differences and execute corrections.
- Support/admin users who maintain distributor credentials, system configuration, and execution visibility.
- Developers or AI agents maintaining the app under the project rules in `AGENTS.md` and `.agents/MEMORY.md`.

## 4. Current Product Scope

### 4.1 Authentication and Session

- Users must sign in before accessing application pages.
- User credentials are validated from Supabase `users_auth`.
- Passwords are stored as bcrypt hashes.
- Failed login attempts are tracked and may trigger lockout.
- Persistent login uses an encrypted `auth_user` cookie.
- Session state must preserve `logged_in`, `current_user`, `last_activity`, bot-running flags, and workflow results.

### 4.2 Dashboard

- Show app-level health and operational summary.
- Show database connection status and bot-running status.
- Provide launcher cards for all available modules.
- Provide a Newspage ping test using configured superuser credentials.
- Show recent activity and full activity report from Supabase logs.
- Attribute runs to the Streamlit user through `run_by` or extraction user fields.

### 4.3 Inventory Adjustment

- Support Auto Compare mode:
  - Select distributor.
  - Extract Newspage stock through Playwright.
  - Upload distributor stock file.
  - Map Newspage and distributor columns.
  - Compare quantities using SKU rules and multiplier rules.
  - Review mismatches before execution.
  - Require a Remark before execution.
  - Auto-fill Remark from uploaded file name when available.
  - Execute adjustments through Newspage Stock Adjustment.
- Support Manual Entry mode:
  - Select distributor.
  - Optionally upload CSV/XLS/XLSX and map columns into manual grid.
  - Edit SKU and PAC/CAR/EA quantities in `st.data_editor`.
  - Require a Remark before execution.
  - Execute valid rows only.
- On successful execution:
  - Capture proof screenshot when available.
  - Send Telegram notification.
  - Provide screenshot download/share controls.

### 4.4 Sales Extraction

- Select distributor and date range.
- Execute Newspage sales extraction through Playwright.
- Package extracted output as ZIP.
- Store output in Streamlit session for download.
- Log extraction history to Supabase.

### 4.5 Promotion Comparison

- Upload SharePoint/MDM tracker workbook.
- Sync promotion data from Newspage using superuser credentials.
- Compare promotion records by promo code and selected fields.
- Flag match, conflict, and missing records.
- Allow download of comparison result and raw Newspage ZIP.

### 4.6 Stock Mutation

- Select source and target distributors.
- Upload mutation file and map SKU, description, and quantity columns.
- Review deduction and addition preview.
- Require Remark before execution.
- Execute source deduction and target addition with separate progress areas.
- Preserve verified mutation logic unless explicitly unlocked by the user.

### 4.7 Clearance Stock

- Select distributor.
- Extract stock data.
- Convert available stock into negative clearance adjustments.
- Review affected SKUs.
- Execute adjustment through the common execution engine.

### 4.8 Initial Stock

- Select distributor.
- Upload initial stock file.
- Map SKU, quantity, and optional description columns.
- Mark non-positive quantities as invalid and skip them during execution.
- Execute valid rows through the common execution engine.

### 4.9 Notifications and Proof

- Telegram alerts are used for bot start, completion, timeout, fatal error, and abort events.
- Success and error screenshots may be captured through Playwright.
- Screenshot files are stored locally under `screenshots/` and ignored by git.
- Client-side WhatsApp sharing must rely on browser-native delegation, not a hosted gateway.

## 5. Non-Functional Requirements

### 5.1 Security

- Never hardcode real credentials in source code.
- Store runtime secrets in `.streamlit/secrets.toml`, deployment secrets, or Supabase.
- Keep `.streamlit/secrets.toml` out of git.
- Encrypt distributor Newspage passwords with Fernet using `MASTER_KEY`.
- Auto-encryption may convert plain-text vault passwords to encrypted values on first fetch.
- Do not expose raw distributor passwords in logs, UI, Telegram messages, or downloadable artifacts.
- Use `html.escape()` before injecting dynamic user-facing values into HTML rendered with `unsafe_allow_html=True`.

### 5.2 Reliability

- Playwright automation must wait for Newspage ASP.NET postbacks before interacting with dependent controls.
- For Newspage UpdatePanel race conditions, use a conservative wait after actions that trigger partial postbacks.
- Failure in one SKU row should update row status and continue where the workflow allows.
- If execution has failures before final save, the document must not be saved to Newspage.
- Dry Run mode must execute the flow without committing final Save/Download actions.

### 5.3 Performance

- Use Streamlit caching for low-risk shared reference data such as system config and distributor lists.
- Avoid expensive recomputation on every rerun where Streamlit session state or fragments can preserve workflow state.
- Keep large extracted data in session state only as long as needed for user download or execution.

### 5.4 UX and Design

- The locked design system is Neo-Brutalism.
- Containers/cards must use sharp corners, thick dark borders, and flat no-blur shadows.
- Buttons must follow the locked border, shadow, hover, and active interaction rules.
- Do not use emoji in UI; use Streamlit Material icons or SVG icons.
- Avoid glassmorphism and rounded corners.
- Mobile layouts must stack cleanly without overlapping controls or clipping text.

### 5.5 Maintainability

- `app.py` owns authentication, global session initialization, CSS injection, and page routing.
- `database.py` owns Supabase access, encryption/decryption, auth, config, and logging.
- `playwright_engine.py` owns browser automation flows.
- `data_processor.py` owns data loading, SKU cleanup, numeric parsing support, and reconciliation logic.
- `utils.py` owns shared UI helpers, CSS loading, responsive table rendering, terminal logs, and Telegram alerts.
- Page modules should remain UI/workflow orchestration layers.

## 6. Data and Integrations

### 6.1 Supabase Tables

- `users_auth`: Streamlit user authentication.
- `login_attempts`: login attempt and lockout state.
- `distributor_vault`: distributor names and Newspage credentials.
- `system_config`: URL, timeout, reason code, warehouse, and UI timing config.
- `sku_formatting_rules`: target SKU mapping/formatting.
- `distributor_sku_multiplier`: distributor-specific quantity multiplier rules.
- `distributor_exceptions` or warehouse exception table: distributor warehouse overrides.
- `adjustment_logs`: stock adjustment and mutation execution records.
- `extraction_history`: inventory and sales extraction history.
- `uploaded_files`: optional uploaded distributor files for audit/download history.

### 6.2 External Systems

- Newspage portal through Playwright Chromium automation.
- Telegram Bot API for notifications.
- Browser Clipboard API for client-side screenshot/text sharing.

## 7. Locked Business Logic

The following feature areas are frozen and must not be refactored or behaviorally changed unless the user explicitly requests it and provides the unlock password defined in `AGENTS.md`:

- Stock Mutation.
- Inventory Adjustment.
- Sales Extraction.
- Promotion Comparison.
- Clearance Stock.
- Initial Stock.
- Credential Auto-Encryption.
- Existing Playwright selectors and execution flow helpers.

Bug fixes should be surgical and should preserve verified behavior unless explicitly authorized.

## 8. Out of Scope

- Replacing Streamlit with another frontend framework.
- Replacing Supabase as the persistence layer.
- Moving Newspage automation away from Playwright.
- Hardcoding distributor credentials in files or code.
- Introducing a non-Neo-Brutalist design language.
- Reintroducing a hosted Telegram-to-WhatsApp gateway.

## 9. Acceptance Criteria

- The application starts from `app.py` and routes to all active modules.
- Users cannot access module pages without authentication.
- Distributor credentials are fetched from Supabase and decrypted at runtime.
- Inventory Adjustment supports extraction, comparison, review, Remark, execution, and proof screenshot flow.
- Sales Extraction produces downloadable ZIP output.
- Promotion Comparison can compare uploaded MDM data against extracted Newspage data.
- Stock Mutation executes source deduction and target addition with separate progress feedback.
- Clearance Stock and Initial Stock can produce execution-ready adjustment rows.
- Dashboard shows operational history and app launcher.
- UI remains consistent with the locked Neo-Brutalism design system.
- Dynamic HTML output escapes user/data-derived strings.
- Python files compile without syntax errors.

## 10. Known Product Risks

- Existing persistent cookies may remain valid until expiry unless revalidated against current user state.
- Dashboard module classification depends on reliable log metadata.
- Manual JavaScript string interpolation can break if data is not serialized safely.
- Streamlit reruns can reset widget-local state if session-state keys are not managed carefully.
- Newspage ASP.NET postback timing can overwrite filters if the bot interacts too early.

