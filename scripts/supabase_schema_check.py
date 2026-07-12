"""Read-only Supabase schema smoke check.

This verifies that required tables and columns are reachable through the
Supabase REST API without printing secrets or row data.
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

REQUIRED_SCHEMA: dict[str, tuple[str, ...]] = {
    "users_auth": ("username", "password", "session_version", "password_changed_at"),
    "login_attempts": ("username", "attempts", "last_attempt", "lockout_until"),
    "distributor_vault": ("nama_distributor", "np_user_id", "np_password"),
    "system_config": ("config_key", "config_value"),
    "sku_formatting_rules": ("sku_code",),
    "distributor_sku_multiplier": ("np_user_id", "sku_target", "multiplier_value"),
    "distributor_exceptions": ("distributor_id", "target_warehouse"),
    "adjustment_logs": ("sku", "qty", "status", "keterangan", "np_user", "run_by", "created_at"),
    "extraction_history": ("distributor_name", "extracted_by", "status", "created_at"),
    "uploaded_files": ("distributor_name", "uploaded_by", "file_name", "file_type", "file_size_bytes", "file_content_base64", "created_at"),
}


@dataclass(frozen=True)
class SchemaCheck:
    table: str
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


def check_table(url: str, key: str, table: str, columns: tuple[str, ...], timeout: int) -> SchemaCheck:
    query = urllib.parse.urlencode({"select": ",".join(columns), "limit": "1"})
    endpoint = f"{url}/rest/v1/{urllib.parse.quote(table)}?{query}"
    request = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Range": "0-0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 300:
                return SchemaCheck(table, "PASS", f"{len(columns)} required column(s) reachable")
            return SchemaCheck(table, "WARN", f"unexpected HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        safe_detail = _summarize_supabase_error(exc.code, body)
        status = "FAIL" if exc.code in (400, 404) else "WARN"
        return SchemaCheck(table, status, safe_detail)
    except Exception as exc:
        return SchemaCheck(table, "WARN", f"{type(exc).__name__}: {exc}")


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


def run_checks(timeout: int = 15) -> list[SchemaCheck]:
    url, key = load_supabase_config()
    if not url or not key:
        return [SchemaCheck("supabase-config", "FAIL", "SUPABASE_URL or SUPABASE_KEY is missing")]
    return [check_table(url, key, table, columns, timeout) for table, columns in REQUIRED_SCHEMA.items()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only Supabase schema checks.")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = run_checks(timeout=args.timeout)
    if args.json:
        print(json.dumps([check.__dict__ for check in checks], indent=2))
    else:
        for check in checks:
            print(f"{check.status:4} {check.table}: {check.detail}")

    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
