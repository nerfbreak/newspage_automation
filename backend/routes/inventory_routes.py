"""Inventory Adjustment API routes.
3-step workflow: Extract -> Compare -> Execute
"""
import io
import re
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from backend.dependencies import get_current_user
from backend.config import get_settings
from backend.core.database import (
    init_supabase, get_system_config, get_distributor_list,
    get_distributor_creds, get_target_skus, get_multiplier_rules,
)
from backend.services import job_manager, data_service
from backend.services.playwright_adapter import run_extract, run_execution
from backend.models import JobStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# In-memory store for extracted DataFrames (keyed by job_id)
_extracted_data: dict[str, dict] = {}


@router.post("/extract")
async def extract_inventory(
    distributor: str = Form(...),
    np_user_id: str = Form(...),
    np_password: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Submit an inventory extraction job."""
    settings = get_settings()
    supabase = init_supabase()
    cfg = get_system_config(supabase)

    try:
        # Reserve the lock first, then get the job object for callbacks
        import threading, uuid
        if not job_manager._playwright_lock.acquire(blocking=False):
            raise RuntimeError("Another Playwright job is already running. Please wait.")

        job_id = str(uuid.uuid4())
        job = job_manager.Job(job_id, "inventory_extract")
        job_manager._jobs[job_id] = job
        _extracted_data[job_id] = {"distributor": distributor, "np_user_id": np_user_id}

        def _hooked_result(r):
            job.result_callback.__func__(r) if hasattr(job.result_callback, '__func__') else None
            if r.get("type") == "dataframe":
                _extracted_data[job_id]["df"] = r["df"]
                _extracted_data[job_id]["filename"] = r.get("filename", "")
            if r.get("type") in ("file", "dataframe", "execution_done"):
                job._push_status("completed")
            elif r.get("type") == "error":
                job._push_status("failed")

        def _run():
            try:
                run_extract(
                    np_user_id, np_password, distributor,
                    cfg["URL_LOGIN"], cfg["TIMEOUT_MS"], cfg["WAREHOUSE"],
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


@router.get("/extract/{job_id}", response_model=JobStatusResponse)
async def get_extract_status(job_id: str, user: dict = Depends(get_current_user)):
    status = job_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.post("/compare")
async def compare_inventory(
    job_id: str = Form(...),
    dist_file: UploadFile = File(...),
    sku_col_np: str = Form(...),
    desc_col_np: str = Form(...),
    qty_col_np: str = Form(...),
    sku_col_dist: str = Form(...),
    qty_col_dist: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Compare extracted NP data with uploaded distributor file."""
    ext = _extracted_data.get(job_id)
    if not ext or "df" not in ext:
        raise HTTPException(status_code=404, detail="Extraction data not found. Run extract first.")

    df_np = ext["df"]
    file_bytes = await dist_file.read()
    if len(file_bytes) > _MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB.")
    df_dist = data_service.load_data_from_bytes(file_bytes, dist_file.filename or "upload.csv")
    if df_dist is None:
        raise HTTPException(status_code=400, detail="Could not parse distributor file.")

    supabase = init_supabase()
    target_skus = get_target_skus(supabase)
    np_user_id = ext.get("np_user_id", "")
    multipliers = get_multiplier_rules(supabase, np_user_id)

    merged, mismatches = data_service.process_compare(
        df_np, df_dist, sku_col_np, desc_col_np, qty_col_np,
        sku_col_dist, qty_col_dist, target_skus, multipliers, np_user_id,
    )

    total_match = len(merged[merged["Status"] == "Match"])
    total_mismatch = len(mismatches)

    # Store comparison result for execution
    _extracted_data[job_id]["merged"] = merged
    _extracted_data[job_id]["mismatches"] = mismatches

    # Convert mismatches to dict list for JSON response
    rows = []
    for _, row in mismatches.iterrows():
        rows.append({
            "sku": str(row.get("SKU", "")),
            "description": str(row.get("Description", "")),
            "newspage": float(row.get("Newspage", 0)),
            "distributor": float(row.get("Distributor", 0)),
            "selisih": float(row.get("Selisih", 0)),
            "status": str(row.get("Status", "")),
        })

    return {
        "total_match": total_match,
        "total_mismatch": total_mismatch,
        "rows": rows,
    }


@router.post("/execute")
async def execute_adjustment(
    job_id: str = Form(...),
    np_user_id: str = Form(...),
    np_password: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Execute stock adjustment based on comparison results."""
    ext = _extracted_data.get(job_id)
    if not ext or "mismatches" not in ext:
        raise HTTPException(status_code=404, detail="Comparison data not found. Run compare first.")

    mismatches = ext["mismatches"]
    if len(mismatches) == 0:
        return {"status": "ok", "message": "No mismatches to adjust."}

    settings = get_settings()
    supabase = init_supabase()
    cfg = get_system_config(supabase)

    # Build execution DataFrame
    df_view = mismatches[["SKU", "Selisih", "Status"]].copy()
    df_view = df_view.rename(columns={"Selisih": "Qty"})
    df_view["Keterangan"] = "Ready to Process"
    df_view["Status"] = df_view["Status"].apply(lambda x: "Pending" if x == "Mismatch" else x)

    distributor = ext.get("distributor", "")

    try:
        import threading, uuid
        if not job_manager._playwright_lock.acquire(blocking=False):
            raise RuntimeError("Another Playwright job is already running. Please wait.")

        exec_job_id = str(uuid.uuid4())
        exec_job = job_manager.Job(exec_job_id, "inventory_execute")
        job_manager._jobs[exec_job_id] = exec_job

        def _run():
            try:
                run_execution(
                    df_view, np_user_id, np_password, distributor,
                    cfg["URL_LOGIN"], cfg["TIMEOUT_MS"], cfg["WAREHOUSE"],
                    cfg["REASON_CODE"], cfg["TABLE_UPDATE_INTERVAL"],
                    exec_job.ui_log, exec_job.alert_callback, supabase,
                    exec_job.progress_callback, exec_job.result_callback,
                )
            finally:
                job_manager._playwright_lock.release()

        exec_job.start(_run, ())
        return {"job_id": exec_job_id, "status": "running"}
    except RuntimeError as e:
        if "Playwright" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise
