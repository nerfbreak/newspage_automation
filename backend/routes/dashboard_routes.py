"""Dashboard API routes - metrics, health, audit logs."""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends

from backend.dependencies import get_current_user
from backend.core.database import init_supabase
from backend.models import DashboardResponse, DashboardMetrics, AuditLogEntry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(user: dict = Depends(get_current_user)):
    supabase = init_supabase()
    db_connected = supabase is not None

    total_extractions = 0
    last_extracted_dist = "N/A"
    last_extracted_time = "N/A"
    total_distributors = 0
    total_logs = 0
    audit_logs: list[AuditLogEntry] = []
    dist_nodes: list[str] = []

    if db_connected:
        # Total extractions
        try:
            res = supabase.table("extraction_history").select("id", count="exact").execute()
            total_extractions = res.count or 0
        except Exception:
            pass

        # Last extraction
        try:
            res = (
                supabase.table("extraction_history")
                .select("distributor_name, created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if res.data:
                last_extracted_dist = res.data[0]["distributor_name"]
                raw_time = res.data[0]["created_at"]
                try:
                    t_str = raw_time.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(t_str)
                    dt_local = dt + timedelta(hours=7)
                    last_extracted_time = dt_local.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    last_extracted_time = raw_time[:16].replace("T", " ")
        except Exception:
            pass

        # Total distributors
        try:
            res = supabase.table("distributor_vault").select("id", count="exact").execute()
            total_distributors = res.count or 0
        except Exception:
            pass

        # Total synced logs
        try:
            res = supabase.table("adjustment_logs").select("id", count="exact").execute()
            total_logs = res.count or 0
        except Exception:
            pass

        # Audit logs (latest 5)
        try:
            res = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(5).execute()
            if res.data:
                audit_logs = [
                    AuditLogEntry(
                        id=r.get("id"),
                        action=r.get("action", ""),
                        details=r.get("details", ""),
                        created_at=r.get("created_at", ""),
                    )
                    for r in res.data
                ]
        except Exception:
            pass

        # Distributor nodes
        try:
            res = supabase.table("distributor_vault").select("nama_distributor").execute()
            dist_nodes = [r["nama_distributor"] for r in res.data] if res.data else []
        except Exception:
            pass

    return DashboardResponse(
        metrics=DashboardMetrics(
            total_extractions=total_extractions,
            last_extracted_dist=last_extracted_dist,
            last_extracted_time=last_extracted_time,
            total_distributors=total_distributors,
            total_logs=total_logs,
            db_connected=db_connected,
            bot_running=False,
            last_sync=last_extracted_time,
        ),
        audit_logs=audit_logs,
        distributor_nodes=dist_nodes,
    )
