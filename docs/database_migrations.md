# Database Migration Notes

**Project**: Optimize Newspage Automation  
**Last reviewed**: 2026-07-06  
**Status**: Documentation baseline only. Do not run in production without checking the live Supabase schema first.

This document records the Supabase tables, columns, and migration expectations used by the application. It exists to close the migration evidence gap identified in `SECURITY_AUDIT_REPORT.md` (`SEC-008`) and to prevent future schema changes from living only in chat history or local memory.

## Source Of Truth

The application currently accesses Supabase through `database.py` and `pages/0_dashboard.py`.

| Table | Current application usage | Required by |
|---|---|---|
| `users_auth` | Login lookup by `username`, reads `password` bcrypt hash | `database.authenticate_user()` |
| `login_attempts` | Tracks failed login count, last attempt, and lockout expiry | `database.check_login_lockout()`, `record_failed_login()`, `reset_failed_login()` |
| `distributor_vault` | Lists distributors and fetches Newspage credentials | `database.get_distributor_list()`, `get_distributor_creds()`, dashboard counts |
| `system_config` | Runtime config values such as URL, timeout, reason code, warehouse | `database.get_system_config()` |
| `sku_formatting_rules` | Target SKU list | `database.get_target_skus()` |
| `distributor_sku_multiplier` | Distributor-specific SKU multiplier rules | `database.get_multiplier_rules()` |
| `distributor_exceptions` | Distributor warehouse override map | `database.get_distributor_warehouse_exceptions()` |
| `adjustment_logs` | Stock adjustment, mutation, clearance, and initial stock execution logs | `database.log_adjustment()`, dashboard history |
| `extraction_history` | Inventory and sales extraction history | `database.log_extraction_history()`, dashboard history |
| `uploaded_files` | Optional uploaded file audit/download history mentioned in PRD and memory | PRD, historical dashboard requirement |

## Baseline Schema Reference

Use this as a setup/review checklist. Prefer additive migrations (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) for existing production tables.

```sql
create table if not exists users_auth (
  id bigserial primary key,
  username text not null unique,
  password text not null,
  created_at timestamptz not null default now()
);

create table if not exists login_attempts (
  username text primary key,
  attempts integer not null default 0,
  last_attempt timestamptz,
  lockout_until timestamptz
);

create table if not exists distributor_vault (
  id bigserial primary key,
  nama_distributor text not null unique,
  np_user_id text not null,
  np_password text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists system_config (
  id bigserial primary key,
  config_key text not null unique,
  config_value text not null,
  updated_at timestamptz not null default now()
);

create table if not exists sku_formatting_rules (
  id bigserial primary key,
  sku_code text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists distributor_sku_multiplier (
  id bigserial primary key,
  np_user_id text not null,
  sku_target text not null,
  multiplier_value numeric not null,
  created_at timestamptz not null default now(),
  unique (np_user_id, sku_target)
);

create table if not exists distributor_exceptions (
  id bigserial primary key,
  distributor_id text not null unique,
  target_warehouse text not null,
  created_at timestamptz not null default now()
);

create table if not exists adjustment_logs (
  id bigserial primary key,
  sku text,
  qty integer not null default 0,
  status text,
  keterangan text,
  np_user text,
  run_by text,
  created_at timestamptz not null default now()
);

create table if not exists extraction_history (
  id bigserial primary key,
  distributor_name text,
  extracted_by text,
  status text not null default 'Success',
  created_at timestamptz not null default now()
);

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
```

## Additive Migration History

These migrations are safe to re-run and should be used when checking an existing Supabase project.

```sql
alter table adjustment_logs
  add column if not exists run_by text;

alter table extraction_history
  add column if not exists status text not null default 'Success';

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
```

## RLS Policy Checklist

Enable RLS deliberately after confirming the key used by the Streamlit app. If the app uses a service-role key server-side only, keep that key out of client code and deployment logs.

```sql
alter table users_auth enable row level security;
alter table login_attempts enable row level security;
alter table distributor_vault enable row level security;
alter table system_config enable row level security;
alter table sku_formatting_rules enable row level security;
alter table distributor_sku_multiplier enable row level security;
alter table distributor_exceptions enable row level security;
alter table adjustment_logs enable row level security;
alter table extraction_history enable row level security;
alter table uploaded_files enable row level security;
```

Minimum review checklist:

- `users_auth.password` contains bcrypt hashes only, never plain text.
- `distributor_vault.np_password` contains Fernet ciphertext (`gAAAA...`) after credential migration.
- `adjustment_logs.run_by` exists so dashboard history can attribute runs to the Streamlit user.
- `extraction_history.status` exists so dashboard can distinguish inventory extraction from sales extraction.
- `uploaded_files` exists only if upload audit/download history is enabled in code.
- No Supabase service-role key is exposed to the browser, committed files, screenshots, or issue threads.
- RLS policies have been reviewed in the Supabase dashboard or SQL editor before enabling anonymous access.

## Operational Change Process

1. Update this document before changing application code that reads or writes Supabase columns.
2. Prefer additive migrations for production tables.
3. Test migrations in a non-production Supabase project first.
4. Confirm dashboard history still loads after schema changes.
5. Update `.agents/MEMORY.md` after the migration documentation or code change is complete.

## Automated RLS & Index Inspection

To verify RLS activation status and index integrity read-only without exposing secrets or row data, use the automated check script:

```powershell
python scripts\supabase_rls_index_check.py
```

To set up the inspection RPC in Supabase (one-time setup in SQL Editor):

```powershell
python scripts\supabase_rls_index_check.py --print-sql
```

Live production status as of 2026-07-08:

- The `verify_rls_and_indexes()` inspection RPC has been installed in Supabase.
- `python scripts\supabase_rls_index_check.py` passes all required checks.
- All 10 required tables have RLS enabled.
- All 10 required tables have at least one index.


