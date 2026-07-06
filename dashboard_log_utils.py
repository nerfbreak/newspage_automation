"""Pure dashboard log shaping helpers.

These helpers intentionally avoid Streamlit and Supabase dependencies so the
dashboard activity logic can be smoke-tested offline.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd


def detect_adjustment_module(qty: Any, full_name: bool = False) -> str:
    """Detect whether an adjustment log row represents stock mutation."""
    qty_text = str(qty)
    is_mutation = "PAC:" in qty_text or "CAR:" in qty_text
    if full_name:
        return "Stock Mutation" if is_mutation else "Inventory Adjustment"
    return "Mutation" if is_mutation else "Inventory"


def detect_extraction_module(status: Any) -> str:
    """Detect whether an extraction history row is sales or inventory."""
    return "Sales" if "(Sales)" in str(status) else "Inventory"


def clean_extraction_status(status: Any) -> str:
    """Remove module marker suffixes from extraction status."""
    return str(status if status is not None else "Success").replace(" (Sales)", "").strip()


def format_dashboard_timestamp(value: Any, include_seconds: bool = False) -> str:
    """Format timestamps for Jakarta dashboard display."""
    fmt = "%Y-%m-%d %H:%M:%S" if include_seconds else "%H:%M - %b %d"
    try:
        ts = pd.Timestamp(value)
        if ts.tzinfo:
            return ts.tz_convert("Asia/Jakarta").strftime(fmt)
        return (ts + timedelta(hours=7)).strftime(fmt)
    except Exception:
        return str(value)[:19 if include_seconds else 16]


def build_recent_activity_rows(
    df_adj: pd.DataFrame,
    df_ext: pd.DataFrame,
    user_to_dist: dict[str, str] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Build recent activity rows from adjustment and extraction dataframes."""
    user_to_dist = user_to_dist or {}
    rows: list[dict[str, Any]] = []

    if df_adj is not None and not df_adj.empty:
        f_adj = df_adj.copy()
        f_adj["created_at"] = pd.to_datetime(f_adj["created_at"])
        f_adj["time_key"] = f_adj["created_at"].dt.floor("min")
        f_adj = f_adj.drop_duplicates(subset=["np_user", "run_by", "time_key", "status"])

        for _, row in f_adj.head(10).iterrows():
            np_user = row.get("np_user", "")
            rows.append(
                {
                    "ts": row["created_at"],
                    "dist": user_to_dist.get(np_user, np_user or "N/A"),
                    "mod": detect_adjustment_module(row.get("qty", "")),
                    "status": row.get("status"),
                    "by": row.get("run_by") or row.get("np_user"),
                }
            )

    if df_ext is not None and not df_ext.empty:
        f_ext = df_ext.copy()
        f_ext["created_at"] = pd.to_datetime(f_ext["created_at"])
        for _, row in f_ext.head(10).iterrows():
            status = row.get("status", "Success")
            rows.append(
                {
                    "ts": row["created_at"],
                    "dist": row.get("distributor_name", "N/A"),
                    "mod": detect_extraction_module(status),
                    "status": clean_extraction_status(status),
                    "by": row.get("extracted_by"),
                }
            )

    rows.sort(key=lambda item: item["ts"], reverse=True)
    return rows[:limit]


def build_full_activity_table_rows(
    df_adj: pd.DataFrame,
    df_ext: pd.DataFrame,
    user_to_dist: dict[str, str] | None = None,
    cutoff_date: Any = None,
    limit: int = 30,
) -> list[dict[str, str]]:
    """Build rendered table rows for the dashboard full activity report."""
    user_to_dist = user_to_dist or {}
    rows: list[dict[str, Any]] = []

    if df_adj is not None and not df_adj.empty:
        f_adj = df_adj.copy()
        f_adj["created_at"] = pd.to_datetime(f_adj["created_at"])
        if cutoff_date is not None:
            f_adj = f_adj[f_adj["created_at"] >= pd.Timestamp(cutoff_date)]
        f_adj["time_key"] = f_adj["created_at"].dt.floor("min")
        f_adj = f_adj.drop_duplicates(subset=["np_user", "run_by", "time_key", "status"])

        for _, row in f_adj.iterrows():
            np_user = row.get("np_user", "")
            rows.append(
                {
                    "ts": row["created_at"],
                    "dist": user_to_dist.get(np_user, np_user or "N/A"),
                    "mod": detect_adjustment_module(row.get("qty", ""), full_name=True),
                    "status": row.get("status", "N/A"),
                    "by": row.get("run_by") or row.get("np_user", "N/A"),
                }
            )

    if df_ext is not None and not df_ext.empty:
        f_ext = df_ext.copy()
        f_ext["created_at"] = pd.to_datetime(f_ext["created_at"])
        if cutoff_date is not None:
            f_ext = f_ext[f_ext["created_at"] >= pd.Timestamp(cutoff_date)]

        for _, row in f_ext.iterrows():
            rows.append(
                {
                    "ts": row["created_at"],
                    "dist": row.get("distributor_name", "N/A"),
                    "mod": "Sales Extraction",
                    "status": row.get("status", "N/A"),
                    "by": row.get("extracted_by", "N/A"),
                }
            )

    rows.sort(key=lambda item: item["ts"], reverse=True)
    table_rows = []
    for row in rows[:limit]:
        table_rows.append(
            {
                "Timestamp": format_dashboard_timestamp(row["ts"], include_seconds=True),
                "Distributor": str(row["dist"]),
                "Module": str(row["mod"]),
                "Status": str(row["status"]).upper(),
                "Run By": str(row["by"]).upper(),
            }
        )
    return table_rows

