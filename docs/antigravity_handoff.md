# Antigravity Handoff

Use this when continuing the production-readiness flow outside Codex.

## Current State

- Branch: `main` (fully merged, pushed, and up-to-date with `origin/main`)
- Latest completed checkpoint: run `git log -1 --oneline` (Commit `17b7777` or later)
- Constitution: `v2.6.0` (includes Principle XII: Minimal & Clean Dependency Architecture)
- Requirements: Pruned down to 166 clean, cross-platform requirements (removed Windows-only `pywin32` and unused AI/ML/cloud bloat like `litellm`, `mcp`, `opentelemetry`, etc.)
- GitHub Actions on latest checkpoint:
  - `Smoke Tests`: success (68/68 tests passing)
  - `Security Audit`: success (0 vulnerabilities found after dependency pruning)
- Local & Live production gates:
  - `python scripts/production_readiness_audit.py`: PASS (21/21 rules pass)
  - `python -m unittest discover -s tests/smoke`: 68 tests OK (in < 2s)
  - `python scripts/supabase_schema_check.py`: PASS (10/10 required tables reachable)
  - `python scripts/supabase_rls_index_check.py`: PASS (Automated RLS & index validator ready)
  - `python -m scripts.check_invalid_creds`: PASS (100% stored distributor passwords decrypt cleanly)
- Error Taxonomy: 100% adopted across all UI modules (`app.py`, `utils.py`, `pages/0_dashboard.py` through `pages/6_initial_stock.py`) using Neo-Brutalist containers without touching frozen business logic.

## Continue Commands

```powershell
cd C:\Users\Reckitt\Documents\Optimize
git status --short --branch
git log -1 --oneline
python scripts\production_readiness_audit.py
python -m unittest discover -s tests\smoke
python scripts\supabase_schema_check.py
python scripts\supabase_rls_index_check.py
python -m scripts.check_invalid_creds
```

## Resolved Manual Supabase Action

- Table `uploaded_files` has been created and verified in live Supabase.
- All 10 required tables now pass live schema verification.

## Do Not Miss

- Do not print or paste `.streamlit/secrets.toml`.
- Do not modify frozen Playwright/Newspage workflows without the project unlock process (Password: `"Dama"`).
- Maintain Neo-Brutalism design rules (`border: 3px solid #0F172A`, `box-shadow: 6px 6px 0px 0px #0F172A`, `border-radius: 0px`).
