# Manual Regression Checklist

**Project**: Optimize Newspage Automation  
**Purpose**: Repeatable smoke/regression checklist for frozen workflows before and after changes.  
**Last Updated**: 2026-07-06

## Rules

- Do not modify frozen business logic while running this checklist.
- Use test-safe distributors, test files, or dry-run mode when possible.
- Capture screenshots or notes for any failed step.
- Stop execution if a workflow appears ready to submit unintended production data.
- Record tester name, date, branch, commit, environment, and result summary.

## Run Header

| Field | Value |
|---|---|
| Date |  |
| Tester |  |
| Branch / Commit |  |
| Environment | Local / Streamlit Cloud / Other |
| Test Data Used |  |
| Overall Result | Pass / Fail / Blocked |

## Global Smoke Checks

- [ ] App starts without syntax/runtime import errors.
- [ ] Login page renders with locked Neo-Brutalism styling.
- [ ] Valid user can log in.
- [ ] Invalid login increments failed-attempt handling.
- [ ] Lockout activates after configured failed-attempt threshold.
- [ ] Logout clears the current session.
- [ ] Login failure/lockout messages display standardized error codes ([AUTH-001], [AUTH-002]) without stack traces.
- [ ] Session expiration toasts display standardized error code ([SESSION-001]).
- [ ] Dashboard loads after login.
- [ ] Sidebar/header remains hidden according to design rules.
- [ ] Main navigation cards route to each module.
- [ ] Footer disclaimer renders.
- [ ] No raw secret, password, token, or stack trace is visible in normal UI.

## Dashboard

- [ ] System health card renders database and engine status.
- [ ] Ping button handles success, failure, and missing credential states without exposing credentials.
- [ ] Ping button failure/missing credential toasts display standardized error codes ([CONFIG-001], [AUTO-001], [AUTO-002], [AUTH-001], [UNK-001]).
- [ ] Dashboard log loading errors display standardized error code ([DB-001]).
- [ ] Recent Activity renders inventory, sales, and adjustment records with correct module labels.
- [ ] Full Activity Report renders without broken HTML.
- [ ] Reporting Period filter changes visible rows as expected.
- [ ] `run_by` or extraction user attribution is visible where data exists.
- [ ] Uploaded file download links appear only when matching uploaded file records exist.
- [ ] Empty database/log states render a friendly message.

## Inventory Adjustment - Auto Compare

- [ ] Distributor dropdown loads expected distributors.
- [ ] Extract action starts only when distributor credentials/config are available.
- [ ] Extraction progress and terminal log update while running.
- [ ] Extracted Newspage data is stored in session and displayed.
- [ ] Distributor stock upload accepts expected CSV/XLSX sample.
- [ ] Uploaded file name auto-fills the Remark field without file extension.
- [ ] Column mapping controls appear for Newspage and distributor fields.
- [ ] Compare step produces matched/mismatched summary.
- [ ] Execution is blocked when Remark is empty.
- [ ] Execution table updates row statuses during run.
- [ ] Successful run logs `run_by` and module/distributor information.
- [ ] Telegram notification and screenshot proof are generated when configured.
- [ ] Clear/reset action returns the module to a clean state.

## Inventory Adjustment - Manual Entry

- [ ] Manual mode opens without depending on Auto Compare state.
- [ ] Optional CSV/XLS/XLSX upload populates preview/mapping.
- [ ] Manual grid supports SKU and PAC/CAR/EA quantity entry.
- [ ] Rows with missing SKU or all zero quantities are ignored or marked invalid.
- [ ] Remark is required before execution.
- [ ] Execution sends only valid rows.
- [ ] Progress, terminal log, final statuses, and proof screenshot render.
- [ ] Clear/reset action removes uploaded/manual data.

## Sales Extraction

- [ ] Distributor dropdown loads expected distributors.
- [ ] Date range controls accept a valid start/end range.
- [ ] Invalid or missing config/credentials produces a safe error.
- [ ] Extraction starts and terminal log updates.
- [ ] Result ZIP is produced and download control appears.
- [ ] `extraction_history` receives a Sales status entry.
- [ ] Telegram notification and screenshot proof are generated when configured.
- [ ] Re-running with a different date range does not reuse stale output.

## Promotion Comparison

- [ ] Tracker workbook upload accepts expected XLSX sample.
- [ ] Required sheets are detected and missing-sheet errors are friendly.
- [ ] Superuser credentials missing state is handled safely.
- [ ] Sync from Newspage starts and shows progress/logging.
- [ ] Comparison output clearly marks match, conflict, and missing records.
- [ ] Result CSV download is generated.
- [ ] Raw Newspage ZIP download is available after successful sync.
- [ ] Uploaded workbook preview does not break responsive table rendering.

## Stock Mutation

- [ ] Source and target distributor dropdowns load.
- [ ] Target distributor cannot be the same as source distributor.
- [ ] Upload accepts expected CSV/XLSX mutation sample.
- [ ] SKU, description, and quantity mapping works.
- [ ] Review table shows deduct and add quantities correctly.
- [ ] Remark is required before execution.
- [ ] Deduct and add executions show separate progress areas.
- [ ] Both terminal logs update independently.
- [ ] Final status box summarizes success/failure.
- [ ] `adjustment_logs` records both sides with correct user attribution.
- [ ] No Playwright selector or core execution logic is changed during testing.

## Clearance Stock

- [ ] Distributor dropdown loads expected distributors.
- [ ] Extract stock action starts and displays progress/logging.
- [ ] Extracted stock converts available stock into negative clearance adjustments.
- [ ] Non-clearable or invalid rows are excluded.
- [ ] Review table renders affected SKUs and quantities.
- [ ] Execution requires expected config/credentials.
- [ ] Final execution statuses and logs render.
- [ ] `adjustment_logs` records clearance adjustment rows.

## Initial Stock

- [ ] Distributor dropdown loads expected distributors.
- [ ] Upload accepts expected CSV/XLSX initial stock sample.
- [ ] SKU and quantity mapping works.
- [ ] Non-positive quantities are marked invalid and skipped.
- [ ] Review table renders valid and invalid rows clearly.
- [ ] Execution sends only valid rows.
- [ ] Progress, terminal log, final statuses, and proof screenshot render.
- [ ] `adjustment_logs` records initial stock rows with user attribution.

## Credential Auto-Encryption

- [ ] Encrypted distributor password decrypts successfully with configured master key.
- [ ] Missing master key produces a safe failure, not silent wrong credentials.
- [ ] Plaintext vault credential migration path is tested only on disposable/test records.
- [ ] Credential values never appear in UI, logs, Telegram messages, screenshots, or downloads.
- [ ] Failed decryption does not corrupt stored credentials.

## File Upload And Download Safety

- [ ] CSV upload with expected delimiter parses correctly.
- [ ] XLSX upload parses expected sheets/columns.
- [ ] Unsupported file extension is rejected by the UI.
- [ ] Oversized or malformed files are handled without crashing the app.
- [ ] Downloaded CSV/ZIP files open and contain expected records.
- [ ] Download file names do not include raw credentials or unsafe path characters.

## Logging And Observability

- [ ] `adjustment_logs` records SKU, quantity, status, distributor/user fields as expected.
- [ ] `extraction_history` records distributor, status, extracted_by, and timestamp.
- [ ] `uploaded_files` records are created only when upload tracking is expected.
- [ ] Dashboard displays new logs after refresh/cache expiry.
- [ ] Failure states produce actionable messages without leaking secrets.
- [ ] Error messages include enough context to diagnose module/distributor/date range.

## Responsive UI Regression

- [ ] Desktop layout remains readable at common laptop width.
- [ ] Mobile layout at 320px stacks buttons and containers without overlap.
- [ ] Mobile layout at 480px keeps forms and data cards readable.
- [ ] Tablet layout at 768px does not clip text or hide primary actions.
- [ ] Wide data tables render as responsive cards where applicable.
- [ ] Neo-Brutalism borders, shadows, colors, and square corners are preserved.

## Completion

- [ ] All failed items have notes and owner.
- [ ] Screenshots/log samples are attached where useful.
- [ ] No production data was unintentionally changed.
- [ ] Any blocker is filed as a bugfix/spec task before merge.
- [ ] Final result is recorded as Pass, Fail, or Blocked.
