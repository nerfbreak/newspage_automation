# Antigravity Handoff

Use this when continuing the production-readiness flow outside Codex.

## Current State

- Branch: `main`
- Remote: `origin/main`
- Latest completed checkpoint: run `git log -1 --oneline` after pulling `origin/main`
- GitHub Actions on latest checkpoint:
  - `Smoke Tests`: success
  - `Security Audit`: success
- Local production gates:
  - `python scripts/production_readiness_audit.py`: PASS
  - `python -m unittest discover -s tests/smoke`: 48 tests OK
- Live Supabase schema check:
  - PASS for all required tables except `uploaded_files`
  - `uploaded_files` migration SQL is documented in `docs/supabase_live_schema_check_2026-07-07.md`

## Continue Commands

```powershell
cd C:\Users\Reckitt\Documents\Optimize
git pull origin main
git status --short --branch
git log -1 --oneline
python scripts\production_readiness_audit.py
python -m unittest discover -s tests\smoke
python scripts\supabase_schema_check.py
```

## Required Manual Supabase Action

Run this in the Supabase SQL Editor for the live project:

```sql
create table if not exists uploaded_files (
  id bigserial primary key,
  distributor_name text,
  uploaded_by text,
  file_name text not null,
  file_type text,
  file_size_bytes bigint,
  file_content_base64 text not null,
  created_at timestamptz not null default now()
);

alter table uploaded_files enable row level security;
```

Then rerun:

```powershell
python scripts\supabase_schema_check.py
```

Expected result: all tables PASS.

## Do Not Miss

- Do not print or paste `.streamlit/secrets.toml`.
- Do not modify frozen Playwright/Newspage workflows without the project unlock process.
- Keep `torch` / `CVE-2025-3000` as a documented exception until a separate dependency-pruning branch proves it is safe to remove or upgrade.
