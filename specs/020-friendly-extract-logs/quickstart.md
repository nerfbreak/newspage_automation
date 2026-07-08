# Quickstart: Friendly Extraction Terminal Logs

## Prerequisites

- Local repository dependencies installed.
- No real Newspage credentials are required for smoke tests.

## Validation Steps

1. Run the focused smoke test:

   ```powershell
   python -m unittest tests.smoke.test_friendly_extract_logs_smoke
   ```

2. Run the full smoke suite:

   ```powershell
   python -m unittest discover -s tests\smoke
   ```

3. Optional manual validation:

   - Open the app.
   - Start Inventory Extraction or Sales Extraction in a safe environment.
   - Confirm terminal messages describe preparation, waiting, downloading, and
     completion in clear operational language.
   - Confirm output files and workflow behavior are unchanged.

## Expected Outcome

- Focused and full smoke tests pass.
- Terminal logs are easier for operations users to understand.
- No selectors, extraction outputs, Supabase logging, or credential handling are
  changed.
