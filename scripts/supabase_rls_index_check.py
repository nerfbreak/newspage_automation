"""Read-only Supabase RLS and Index automation check.

This script verifies Row Level Security (RLS) activation status and index
integrity for all required production tables via the Supabase REST API (RPC)
without exposing secrets or modifying data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SECRETS_FILE = REPO_ROOT / ".streamlit" / "secrets.toml"

REQUIRED_TABLES: tuple[str, ...] = (
    "users_auth",
    "login_attempts",
    "distributor_vault",
    "system_config",
    "sku_formatting_rules",
    "distributor_sku_multiplier",
    "distributor_exceptions",
    "adjustment_logs",
    "extraction_history",
    "uploaded_files",
)

SETUP_SQL = """-- Read-only Supabase RLS & Index inspection helper
-- Run this once in the Supabase SQL Editor for your project.

create or replace function verify_rls_and_indexes()
returns jsonb
language plpgsql
security definer
as $$
declare
  result jsonb;
begin
  select jsonb_build_object(
    'rls_status', (
      select jsonb_agg(jsonb_build_object(
        'table', tablename,
        'rls_enabled', rowsecurity
      ) order by tablename)
      from pg_tables
      where schemaname = 'public' and tablename in (
        'users_auth', 'login_attempts', 'distributor_vault', 'system_config',
        'sku_formatting_rules', 'distributor_sku_multiplier', 'distributor_exceptions',
        'adjustment_logs', 'extraction_history', 'uploaded_files'
      )
    ),
    'indexes', (
      select jsonb_agg(jsonb_build_object(
        'table', tablename,
        'index_name', indexname,
        'index_def', indexdef
      ) order by tablename, indexname)
      from pg_indexes
      where schemaname = 'public' and tablename in (
        'users_auth', 'login_attempts', 'distributor_vault', 'system_config',
        'sku_formatting_rules', 'distributor_sku_multiplier', 'distributor_exceptions',
        'adjustment_logs', 'extraction_history', 'uploaded_files'
      )
    )
  ) into result;
  return result;
end;
$$;

grant execute on function verify_rls_and_indexes() to anon, authenticated;
"""


@dataclass(frozen=True)
class RLSIndexCheck:
    table: str
    check_type: str
    status: str
    detail: str


def _load_local_secrets() -> dict[str, str]:
    if not SECRETS_FILE.is_file():
        return {}
    with SECRETS_FILE.open("rb") as handle:
        data = tomllib.load(handle)
    return {str(key): str(value) for key, value in data.items()}


def load_supabase_config() -> tuple[str, str]:
    secrets = _load_local_secrets()
    url = os.environ.get("SUPABASE_URL") or secrets.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY") or secrets.get("SUPABASE_KEY", "")
    return url.rstrip("/"), key


def check_rls_and_indexes(url: str, key: str, timeout: int) -> list[RLSIndexCheck]:
    endpoint = f"{url}/rest/v1/rpc/verify_rls_and_indexes"
    request = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        data=b"{}",
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 300:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
                return _parse_rpc_response(payload)
            return [RLSIndexCheck("all", "rpc", "WARN", f"unexpected HTTP {response.status}")]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return [
                RLSIndexCheck(
                    "all",
                    "rpc",
                    "WARN",
                    "RPC 'verify_rls_and_indexes' not found. Run with --print-sql to get setup SQL.",
                )
            ]
        body = exc.read().decode("utf-8", errors="replace")
        safe_detail = _summarize_supabase_error(exc.code, body)
        return [RLSIndexCheck("all", "rpc", "FAIL" if exc.code == 400 else "WARN", safe_detail)]
    except Exception as exc:
        return [RLSIndexCheck("all", "rpc", "WARN", f"{type(exc).__name__}: {exc}")]


def _parse_rpc_response(payload: dict) -> list[RLSIndexCheck]:
    checks: list[RLSIndexCheck] = []
    rls_list = payload.get("rls_status") or []
    index_list = payload.get("indexes") or []

    rls_map = {row["table"]: row.get("rls_enabled", False) for row in rls_list if isinstance(row, dict)}
    indexes_by_table: dict[str, list[str]] = {}
    for idx in index_list:
        if isinstance(idx, dict) and "table" in idx:
            tbl = str(idx["table"])
            indexes_by_table.setdefault(tbl, []).append(str(idx.get("index_name", "unknown")))

    for table in REQUIRED_TABLES:
        if table in rls_map:
            enabled = rls_map[table]
            if enabled:
                checks.append(RLSIndexCheck(table, "RLS", "PASS", "RLS is enabled"))
            else:
                checks.append(RLSIndexCheck(table, "RLS", "FAIL", "RLS is NOT enabled"))
        else:
            checks.append(RLSIndexCheck(table, "RLS", "WARN", "Table missing from live inspection"))

        tbl_indexes = indexes_by_table.get(table, [])
        if tbl_indexes:
            checks.append(
                RLSIndexCheck(table, "INDEX", "PASS", f"{len(tbl_indexes)} index(es) found: {', '.join(tbl_indexes)}")
            )
        else:
            checks.append(RLSIndexCheck(table, "INDEX", "WARN", "No indexes found for table"))

    return checks


def _summarize_supabase_error(status_code: int, body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return f"HTTP {status_code}"

    code = payload.get("code", "unknown")
    message = str(payload.get("message", "Supabase request failed"))
    hint = str(payload.get("hint", "") or "")
    summary = f"HTTP {status_code} {code}: {message}"
    if hint:
        summary += f" Hint: {hint}"
    return summary


def run_checks(timeout: int = 15) -> list[RLSIndexCheck]:
    url, key = load_supabase_config()
    if not url or not key:
        return [RLSIndexCheck("supabase-config", "config", "FAIL", "SUPABASE_URL or SUPABASE_KEY is missing")]
    return check_rls_and_indexes(url, key, timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only Supabase RLS and Index checks.")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--print-sql", action="store_true", help="Print SQL to set up the inspection RPC in Supabase")
    args = parser.parse_args()

    if args.print_sql:
        print(SETUP_SQL.strip())
        return 0

    checks = run_checks(timeout=args.timeout)
    if args.json:
        print(json.dumps([check.__dict__ for check in checks], indent=2))
    else:
        for check in checks:
            print(f"{check.status:4} [{check.check_type:5}] {check.table}: {check.detail}")

    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
