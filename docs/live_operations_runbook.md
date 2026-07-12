# Live Operations Runbook

This runbook is for operating Optimize Newspage Automation after release to active users.

## Operating Principles

- Treat `main` as the deployable production branch.
- Do not bypass the release readiness gate for production changes.
- Do not modify frozen Newspage automation logic without the unlock process in `AGENTS.md`.
- Do not commit `.streamlit/secrets.toml`, `.env`, screenshots, downloaded user files, Supabase exports, or credential dumps.
- Prefer Dry Run checks before any operator performs a mutating Newspage action.

## Daily Health Check

Run or confirm these at the start of each operating day:

```powershell
python scripts/production_readiness_audit.py
python -m unittest discover -s tests/smoke
```

Live checks:

- `https://newspage.streamlit.app/healthz` returns HTTP `200` and `{"status":"ok"}`.
- GitHub `Smoke Tests` badge is passing.
- GitHub `Security Audit` badge is passing.
- GitHub `Release Readiness` badge is passing.
- Dashboard opens after sign-in and does not show a Streamlit traceback.
- Dashboard database status is healthy.

## Weekly Maintenance

- Review Dependabot pull requests for `pip` and GitHub Actions updates.
- Merge dependency updates only after `Smoke Tests`, `Security Audit`, and `Release Readiness` pass.
- Review `SECURITY_AUDIT_REPORT.md` if a dependency scan introduces a new advisory or ignore.
- Run `python scripts/supabase_schema_check.py` against live Supabase.
- Run `python scripts/supabase_rls_index_check.py` against live Supabase.
- Run `python -m scripts.check_invalid_creds` to verify stored distributor credentials still decrypt cleanly.

## User Onboarding

Before giving a user access:

- Create or confirm their `users_auth` record in Supabase.
- Use a bcrypt password hash, never a plain-text password.
- Set or rotate `session_version` when password access changes.
- Confirm the user can sign in and reach the dashboard.
- Confirm the user understands Dry Run mode and when final Newspage Save actions are allowed.
- Confirm the user knows where to report failures and which screenshot/log evidence to include.

## Access Revocation

When removing access:

- Disable or delete the user's `users_auth` record.
- Rotate `session_version` if the account remains present.
- Reboot the Streamlit app if active sessions must be flushed quickly.
- Confirm an already-open tab returns to the sign-in page on reload.
- Record the access change in the operating notes or support tracker.

## Incident Triage

Use this order when a live user reports a problem:

1. Check `/healthz`.
2. Check GitHub workflow badges.
3. Check whether the issue happens before or after login.
4. Check whether the issue is isolated to one module, one distributor, one uploaded file, or all users.
5. Check Supabase schema/RLS/index gates.
6. Check distributor credential decrypt health.
7. Ask the user for the module name, distributor, timestamp, uploaded file name, and screenshot proof if available.
8. If a frozen automation workflow may be affected, stop and use the locked unlock process before code changes.

## Rollback

Rollback when:

- `/healthz` fails.
- Users cannot sign in.
- Dashboard shows a Streamlit traceback.
- Supabase schema/RLS/index checks fail.
- A release workflow fails on `main`.
- A frozen workflow regresses during a controlled live operator test.

Rollback steps:

1. Revert or redeploy the last known-good commit.
2. Reboot Streamlit Cloud.
3. Confirm `/healthz` is healthy.
4. Run a sign-in smoke test.
5. Confirm dashboard and module routing.
6. Record the rollback in `.agents/MEMORY.md` and `docs/production_readiness_status.md`.

## Evidence To Keep

For every release or incident, keep:

- Release commit SHA.
- GitHub workflow status.
- Live `/healthz` result.
- Supabase schema/RLS/index result.
- Manual regression outcome.
- Any rollback or mitigation decision.
