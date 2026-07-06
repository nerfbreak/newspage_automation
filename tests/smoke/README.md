# Smoke Tests

These tests are intentionally small, offline, and safe to run before a checkpoint.

Run from the project root:

```powershell
python -m unittest discover -s tests/smoke
```

Use the same Python environment that runs the app dependencies (`pandas`, `streamlit`, and `supabase` must be importable).

Coverage focus:

- Login lockout and reset behavior using a fake Supabase client.
- Dashboard activity log shaping without live Supabase or Streamlit rendering.
- CSV and ZIP upload parsing with in-memory files.
- Core numeric parsing used by upload and comparison flows.
- SKU cleanup and comparison output shape.
- Responsive dataframe HTML escaping.
- Error taxonomy formatting and fallback behavior.

These tests do not log in to Newspage, open Playwright, call Supabase, send Telegram messages, or execute frozen automation workflows.
