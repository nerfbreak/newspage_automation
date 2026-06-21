"""Sales Extraction API routes."""
import re
import logging
import uuid
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response

from backend.dependencies import get_current_user
from backend.config import get_settings
from backend.core.database import init_supabase, get_system_config
from backend.services import job_manager
from backend.services.playwright_adapter import run_sales_extract

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory file store for downloads
_sales_files: dict[str, dict] = {}


@router.post("/extract")
async def extract_sales(
    distributor: str = Form(...),
    np_user_id: str = Form(...),
    np_password: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Submit a sales extraction job."""
    settings = get_settings()
    supabase = init_supabase()
    cfg = get_system_config(supabase)

    try:
        if not job_manager._playwright_lock.acquire(blocking=False):
            raise RuntimeError("Another Playwright job is already running. Please wait.")

        job_id = str(uuid.uuid4())
        job = job_manager.Job(job_id, "sales_extract")
        job_manager._jobs[job_id] = job

        def _hooked_result(r):
            if r.get("type") == "file":
                _sales_files[job_id] = {
                    "data": r["data"],
                    "filename": r.get("filename", "sales.csv"),
                }
                job.file_data = r["data"]
                job.file_name = r.get("filename", "sales.csv")
                job._push_file_ready(f"/api/sales/download/{job_id}", job.file_name)
                job._push_status("completed")
            elif r.get("type") == "error":
                job._push_status("failed")

        def _run():
            try:
                run_sales_extract(
                    np_user_id, np_password, distributor,
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


@router.get("/download/{job_id}")
async def download_sales(job_id: str, user: dict = Depends(get_current_user)):
    """Download the extracted sales CSV file."""
    file_info = _sales_files.get(job_id)
    if not file_info:
        # Also check job object
        job = job_manager.get_job(job_id)
        if job and job.file_data:
            file_info = {"data": job.file_data, "filename": job.file_name}

    if not file_info:
        raise HTTPException(status_code=404, detail="File not found. Extraction may still be running.")

    safe_name = re.sub(r'[^\w\-. ]', '', file_info["filename"])
    return Response(
        content=file_info["data"],
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
