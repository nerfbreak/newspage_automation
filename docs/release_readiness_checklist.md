# Release Readiness Checklist

This checklist is the release gate for Optimize Newspage Automation before the app is announced as ready for broad internal use.

## Release Candidate Inputs

- Target branch: `main`
- Deployment: Streamlit Cloud at `https://newspage.streamlit.app`
- Runtime secrets: Streamlit Cloud secrets and Supabase, never committed to git
- Required app entry point: `app.py`
- Required database baseline: `docs/database_migrations.md`
- Required manual regression scope: `tests/manual/REGRESSION_CHECKLIST.md`
- Required live operations runbook: `docs/live_operations_runbook.md`

## Automated Gates

Run these from the repository root before every release candidate:

```powershell
python scripts/production_readiness_audit.py
python -m unittest discover -s tests/smoke
python scripts/supabase_schema_check.py
python scripts/supabase_rls_index_check.py
python -m scripts.check_invalid_creds
```

Dependency security must pass in CI:

```powershell
python -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off --ignore-vuln CVE-2025-3000
```

The ignored `CVE-2025-3000` entry is the current pip-audit advisory noise already reviewed in the security audit flow. Do not add new ignores without recording the reason in `SECURITY_AUDIT_REPORT.md`.

## GitHub Actions Gates

The following workflows must be green on the release commit:

- `Smoke Tests`
- `Security Audit`
- `Release Readiness`

The `Release Readiness` workflow runs automatically on pushes and pull requests targeting `main`. It can also be run manually with `workflow_dispatch` after Streamlit Cloud has deployed the intended commit.

## Live Deployment Gates

After Streamlit Cloud deploys the release commit:

1. Open `https://newspage.streamlit.app/healthz`.
2. Confirm it returns HTTP `200` and `{"status":"ok"}`.
3. Open `https://newspage.streamlit.app`.
4. Confirm the sign-in page renders.
5. Log in with the current test account.
6. Confirm the dashboard renders without a Streamlit traceback.
7. Confirm database connection status is healthy on the dashboard.
8. Open each module from the dashboard launcher.
9. Confirm Dry Run mode is available before testing automation flows.
10. Do not execute mutating Newspage actions during release smoke unless an operator explicitly approves the exact distributor and file.

## Session And Credential Gates

Before broad release:

- Rotate the shared test account password.
- Confirm rotating `users_auth.session_version` invalidates remembered cookies and already-open authenticated tabs.
- Confirm `.streamlit/secrets.toml`, `.env`, exported Supabase dumps, screenshots, and downloaded user files are not tracked by git.
- Confirm `python -m scripts.check_invalid_creds` reports every stored distributor credential decrypts cleanly.

## Manual Regression Gates

Use `tests/manual/REGRESSION_CHECKLIST.md` for the manual pass. At minimum, cover:

- Authentication and sign-out.
- Dashboard activity rendering.
- Inventory Adjustment Dry Run path.
- Sales Extraction navigation and date validation.
- Promotion Comparison upload validation.
- Stock Mutation preview validation.
- Clearance Stock preview validation.
- Initial Stock upload validation.

The manual pass should avoid final Newspage Save clicks unless the release owner authorizes a controlled live run.

## Rollback Plan

Rollback is required if any of these occur after release:

- `/healthz` is not `200`.
- Users cannot log in.
- Dashboard renders a traceback.
- Supabase schema or RLS/index checks fail.
- Smoke tests or the static production audit fail on the release commit.
- A frozen automation workflow regresses in a live operator test.

Rollback steps:

1. Revert the release commit or redeploy the last known-good commit from Streamlit Cloud.
2. Reboot the Streamlit Cloud app.
3. Re-check `/healthz`.
4. Run the live sign-in smoke test.
5. Record the rollback reason in `.agents/MEMORY.md` and `docs/production_readiness_status.md`.

## Release Decision

A release can be marked ready only when:

- Local static production audit passes.
- Local smoke suite passes.
- Supabase schema and RLS/index checks pass.
- GitHub `Smoke Tests`, `Security Audit`, and `Release Readiness` are green on the release commit.
- Live Streamlit Cloud smoke passes after deployment.
- The automated `Live Health Probe` job passes for the release commit on `main`.
- Manual regression checklist has no blocking issue.
- Live operators have reviewed `docs/live_operations_runbook.md`.
- Rollback plan is understood by the release owner.
