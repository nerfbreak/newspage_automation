# Supabase Live Schema Check - 2026-07-07

**Mode**: Read-only Supabase REST schema check  
**Data exposure**: No row data or secrets printed  
**Command**:

```powershell
python scripts/supabase_schema_check.py
```

## Result

| Table | Status | Notes |
|---|---|---|
| `users_auth` | PASS | Required columns reachable |
| `login_attempts` | PASS | Required columns reachable |
| `distributor_vault` | PASS | Required columns reachable |
| `system_config` | PASS | Required columns reachable |
| `sku_formatting_rules` | PASS | Required columns reachable |
| `distributor_sku_multiplier` | PASS | Required columns reachable |
| `distributor_exceptions` | PASS | Required columns reachable |
| `adjustment_logs` | PASS | Includes `run_by` |
| `extraction_history` | PASS | Includes `status` |
| `uploaded_files` | FAIL | Table missing from live Supabase schema cache |

## Required Migration

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

After applying the migration, rerun:

```powershell
python scripts/supabase_schema_check.py
```

Expected result: all tables PASS.
