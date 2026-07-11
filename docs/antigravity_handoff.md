# Antigravity Handoff

Use this when continuing the operations flow in Antigravity.

## Current State

- Branch: `main` (fully merged, pushed, and up-to-date with `origin/main`)
- Latest completed features:
  - **Spec-035 (Bot Task Monitor Dashboard)**: Realtime active task tracking connected with Playwright lifecycle hooks.
  - **Spec-036 (Mutation Auto-Approve)**: Added full auto-approve postback execution on Stock Mutation logic specifically targeting `SA3` and `SA4` reason codes, ensuring screenshots capture the Approved state.
  - **UI/UX Polishes**: Added *Copy/Download* buttons to Stock Mutation screenshots, extended global `max_chars` to 100 on remarks, fixed table/UI alignments in split columns.
- Constitution: `v2.6.0` (includes Principle XII: Minimal & Clean Dependency Architecture)
- Testing & Gates:
  - `python -m pytest tests/smoke/`: 103 tests passing.
  - `python scripts/production_readiness_audit.py`: PASS
  - AST Verification checks on core modules: PASS
- Live Deployments: Code has been pushed and is running on Streamlit Cloud.

## Continue Commands

```powershell
cd C:\Users\Reckitt\Documents\Optimize
git pull
git status --short --branch
git log -3 --oneline
python scripts\production_readiness_audit.py
python -m pytest tests\smoke -q --tb=short
```

## Do Not Miss

- Do not print or paste `.streamlit/secrets.toml`.
- Do not modify frozen Playwright/Newspage workflows without the project unlock process (Password: `"Dama"`).
- Maintain Neo-Brutalism design rules (`border: 3px solid #0F172A`, `box-shadow: 6px 6px 0px 0px #0F172A`, `border-radius: 0px`).
- Pay attention to `_capture_stkadj_success_screenshot` inside `playwright_engine.py` if there are any lingering ASP.NET postback visibility bugs on slow networks.
