"""Promotion Comparison API routes."""
import io
import logging
import re
import uuid
import zipfile
from datetime import datetime, timezone, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import Response

from backend.dependencies import get_current_user
from backend.config import get_settings
from backend.core.database import init_supabase, get_system_config
from backend.services import job_manager
from backend.services.playwright_adapter import run_promotion_sync

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# In-memory file store for downloads
_promo_files: dict[str, dict] = {}
_comparison_cache: dict[str, pd.DataFrame] = {}


@router.post("/sync")
async def sync_promotion(
    start_date: str = Form(...),
    end_date: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Submit a promotion sync job using superuser credentials."""
    settings = get_settings()
    supabase = init_supabase()
    cfg = get_system_config(supabase)

    bot_user = settings.np_user_super
    bot_pass = settings.np_pass_super
    if not bot_user or not bot_pass:
        raise HTTPException(status_code=400, detail="Superuser credentials not configured.")

    try:
        if not job_manager._playwright_lock.acquire(blocking=False):
            raise RuntimeError("Another Playwright job is already running. Please wait.")

        job_id = str(uuid.uuid4())
        job = job_manager.Job(job_id, "promotion_sync")
        job_manager._jobs[job_id] = job

        def _hooked_result(r):
            if r.get("type") == "file":
                _promo_files[job_id] = {
                    "data": r["data"],
                    "filename": r.get("filename", "promo.zip"),
                }
                job.file_data = r["data"]
                job.file_name = r.get("filename", "promo.zip")
                job._push_file_ready(f"/api/promotion/download/{job_id}", job.file_name)
                job._push_status("completed")
            elif r.get("type") == "error":
                job._push_status("failed")

        def _run():
            try:
                run_promotion_sync(
                    bot_user, bot_pass, "GLOBAL",
                    cfg["URL_LOGIN"], cfg["TIMEOUT_MS"],
                    start_date, end_date,
                    job.ui_log, job.alert_callback, supabase, user["username"],
                    _hooked_result,
                )
            finally:
                job_manager._playwright_lock.release()

        job.start(_run, ())
        return {"job_id": job_id, "status": "running"}
    except RuntimeError as e:
        if "Playwright" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise


@router.post("/compare")
async def compare_promotion(
    job_id: str = Form(...),
    sharepoint_file: UploadFile = File(...),
    filter_status: str = Form("All"),
    user: dict = Depends(get_current_user),
):
    """Compare Newspage promo data with SharePoint Excel."""
    promo = _promo_files.get(job_id)
    if not promo:
        job = job_manager.get_job(job_id)
        if job and job.file_data:
            promo = {"data": job.file_data, "filename": job.file_name}

    if not promo:
        raise HTTPException(status_code=404, detail="Promo data not found. Run sync first.")

    # Read SharePoint Excel
    try:
        file_bytes = await sharepoint_file.read()
        if len(file_bytes) > _MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB.")
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        mdm_data = None
        if "tracker MDM" in xl.sheet_names:
            mdm_data = pd.read_excel(xl, sheet_name="tracker MDM")
        if mdm_data is None:
            raise HTTPException(status_code=400, detail="Sheet 'tracker MDM' not found in file.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error reading SharePoint Excel: %s", e)
        raise HTTPException(status_code=400, detail="Error reading Excel file. Ensure the format is correct.")

    # Parse Newspage ZIP
    try:
        all_np_rows = []
        with zipfile.ZipFile(io.BytesIO(promo["data"])) as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        df_temp = pd.read_csv(f, sep='|', encoding='utf-8')
                        all_np_rows.append(df_temp)

        if not all_np_rows:
            raise HTTPException(status_code=400, detail="No CSV data found in extraction ZIP.")

        df_np_total = pd.concat(all_np_rows, ignore_index=True)
        df_np_total.columns = [c.strip().upper() for c in df_np_total.columns]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error parsing Newspage data: %s", e)
        raise HTTPException(status_code=400, detail="Error parsing Newspage extraction data. Ensure the ZIP file is valid.")

    # Comparison logic (mirrors pages/3_promotion_comparison.py)
    df_sp = mdm_data.copy()
    sp_code_col = 'Promo Code (20)' if 'Promo Code (20)' in df_sp.columns else df_sp.columns[0]
    np_code_col = 'PROMO_CODE' if 'PROMO_CODE' in df_np_total.columns else df_np_total.columns[0]

    df_sp[sp_code_col] = df_sp[sp_code_col].astype(str).str.strip().str.upper()
    df_np_total[np_code_col] = df_np_total[np_code_col].astype(str).str.strip().str.upper()

    df_merge = pd.merge(
        df_sp, df_np_total,
        left_on=sp_code_col, right_on=np_code_col,
        how='left', suffixes=('_SP', '_NP'),
    )

    def validate_promo(row):
        if pd.isnull(row[np_code_col]):
            return "MISSING", "Promo not found in Newspage"
        issues = []
        try:
            sp_start = pd.to_datetime(row.get('Start Date', None))
            sp_end = pd.to_datetime(row.get('End Date', None))
            np_start = pd.to_datetime(row.get('START_DATE', None))
            np_end = pd.to_datetime(row.get('END_DATE', None))
            if pd.notnull(sp_start) and pd.notnull(np_start):
                if sp_start.date() != np_start.date():
                    issues.append(f"Start Date Mismatch ({sp_start.date()} vs {np_start.date()})")
            if pd.notnull(sp_end) and pd.notnull(np_end):
                if sp_end.date() != np_end.date():
                    issues.append(f"End Date Mismatch ({sp_end.date()} vs {np_end.date()})")
        except Exception:
            pass
        sp_status = str(row.get('Promo Status', '')).strip().upper()
        np_status = str(row.get('STATUS', '')).strip().upper()
        if sp_status and np_status and sp_status[0] != np_status[0]:
            issues.append(f"Status Conflict ({sp_status} vs {np_status})")
        return ("MATCH", "All good") if not issues else ("CONFLICT", " | ".join(issues))

    results = df_merge.apply(validate_promo, axis=1, result_type='expand')
    df_merge['MATCH_STATUS'] = results[0]
    df_merge['ISSUE_DETAILS'] = results[1]

    _comparison_cache[job_id] = df_merge

    # Apply filter
    df_view = df_merge if filter_status == "All" else df_merge[df_merge['MATCH_STATUS'] == filter_status]

    match_count = len(df_merge[df_merge['MATCH_STATUS'] == 'MATCH'])
    conflict_count = len(df_merge[df_merge['MATCH_STATUS'] == 'CONFLICT'])
    missing_count = len(df_merge[df_merge['MATCH_STATUS'] == 'MISSING'])

    # Convert to CSV for download
    csv_buffer = io.StringIO()
    df_view.to_csv(csv_buffer, index=False)

    return {
        "match_count": match_count,
        "conflict_count": conflict_count,
        "missing_count": missing_count,
        "csv_data": csv_buffer.getvalue(),
    }


@router.get("/download/{job_id}")
async def download_promotion(job_id: str, user: dict = Depends(get_current_user)):
    """Download raw Newspage promo extraction ZIP."""
    promo = _promo_files.get(job_id)
    if not promo:
        job = job_manager.get_job(job_id)
        if job and job.file_data:
            promo = {"data": job.file_data, "filename": job.file_name}

    if not promo:
        raise HTTPException(status_code=404, detail="File not found.")

    safe_name = re.sub(r'[^\w\-. ]', '', promo["filename"])
    return Response(
        content=promo["data"],
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.get("/download/{job_id}/comparison")
async def download_comparison(job_id: str, user: dict = Depends(get_current_user)):
    """Download promotion comparison CSV."""
    df = _comparison_cache.get(job_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Comparison not found. Run compare first.")

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    now = datetime.now(timezone(timedelta(hours=7)))
    filename = f"promo_comparison_{now.strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
