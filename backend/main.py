"""FastAPI backend for Optimize Newspage Automation Engine.
Serves as the API layer between the Android client and the Playwright automation.
"""
import re
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.services import job_manager
from backend.dependencies import get_current_user
from backend.routes import (
    auth_routes,
    dashboard_routes,
    distributor_routes,
    inventory_routes,
    sales_routes,
    promotion_routes,
    ws_routes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = time.time()
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("FATAL: JWT_SECRET is not configured. Server cannot start.")
    logger.info("Starting Optimize API backend")
    logger.info("Supabase URL configured: %s", bool(settings.supabase_url))
    yield
    logger.info("Shutting down Optimize API backend")


app = FastAPI(
    title="Optimize Newspage API",
    description="Backend API for the Newspage Automation Android client",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - restrict to known origins
_allowed_origins = [
    "http://localhost:8501",       # Streamlit local
    "http://localhost:8000",       # FastAPI local
    "http://10.0.2.2:8000",       # Android emulator
    "https://optimize-newspage-api-production-2338.up.railway.app",  # Railway
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(distributor_routes.router, prefix="/api/distributors", tags=["Distributors"])
app.include_router(inventory_routes.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(sales_routes.router, prefix="/api/sales", tags=["Sales"])
app.include_router(promotion_routes.router, prefix="/api/promotion", tags=["Promotion"])
app.include_router(ws_routes.router, tags=["WebSocket"])


@app.get("/api/health")
async def health_check():
    uptime = time.time() - _start_time if _start_time else 0
    return {"status": "ok", "uptime": round(uptime, 2)}


@app.get("/api/download/{job_id}")
async def download_file(job_id: str, user: dict = Depends(get_current_user)):
    """Generic file download endpoint (requires authentication)."""
    from fastapi.responses import Response
    job = job_manager.get_job(job_id)
    if not job or not job.file_data:
        raise HTTPException(status_code=404, detail="File not found")
    content_type = "application/octet-stream"
    safe_name = re.sub(r'[^\w\-. ]', '', job.file_name)
    if safe_name.endswith(".csv"):
        content_type = "text/csv"
    elif safe_name.endswith(".zip"):
        content_type = "application/zip"
    return Response(
        content=job.file_data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
