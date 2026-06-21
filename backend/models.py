"""Pydantic request/response schemas for all API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================
# Auth
# ============================================================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    ok: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None
    locked: bool = False
    remaining: int = 0
    attempts_left: int = 0


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    ok: bool
    access_token: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None


# ============================================================
# Dashboard
# ============================================================
class DashboardMetrics(BaseModel):
    total_extractions: int = 0
    last_extracted_dist: str = "N/A"
    last_extracted_time: str = "N/A"
    total_distributors: int = 0
    total_logs: int = 0
    db_connected: bool = False
    bot_running: bool = False
    last_sync: str = "N/A"


class AuditLogEntry(BaseModel):
    id: Optional[int] = None
    action: str = ""
    details: str = ""
    created_at: str = ""


class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    audit_logs: list[AuditLogEntry] = []
    distributor_nodes: list[str] = []


# ============================================================
# Distributors
# ============================================================
class DistributorListResponse(BaseModel):
    distributors: list[str]


class DistributorCredentials(BaseModel):
    np_user_id: str
    has_password: bool


# ============================================================
# Inventory Adjustment
# ============================================================
class InventoryExtractRequest(BaseModel):
    distributor: str
    np_user_id: str
    np_password: str


class InventoryCompareRequest(BaseModel):
    """Client sends column mapping + file data as base64 or multipart."""
    sku_col_np: str
    desc_col_np: str
    qty_col_np: str
    sku_col_dist: str
    qty_col_dist: str


class ComparisonRow(BaseModel):
    sku: str
    description: str = ""
    newspage: float = 0
    distributor: float = 0
    selisih: float = 0
    status: str = "Match"


class ComparisonResult(BaseModel):
    total_match: int
    total_mismatch: int
    rows: list[ComparisonRow]


class ExecuteRequest(BaseModel):
    distributor: str
    np_user_id: str
    np_password: str
    adjustments: list[dict]  # [{sku, qty, status}]


# ============================================================
# Sales Extraction
# ============================================================
class SalesExtractRequest(BaseModel):
    distributor: str
    np_user_id: str
    np_password: str
    start_date: str  # DD/MM/YYYY
    end_date: str    # DD/MM/YYYY


# ============================================================
# Promotion Comparison
# ============================================================
class PromotionSyncRequest(BaseModel):
    start_date: str  # DD/MM/YYYY
    end_date: str    # DD/MM/YYYY


class PromotionCompareRequest(BaseModel):
    filter_status: str = "All"  # All, MATCH, CONFLICT, MISSING


# ============================================================
# Job status
# ============================================================
class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, running, completed, failed
    progress: Optional[int] = None
    total: Optional[int] = None
    message: str = ""


# ============================================================
# WebSocket messages (server -> client)
# ============================================================
class WSLogMessage(BaseModel):
    type: str = "log"  # log, progress, status, file_ready, ping
    module: str = ""
    msg: str = ""
    timestamp: str = ""
    elapsed_ms: int = 0


class WSProgressMessage(BaseModel):
    type: str = "progress"
    current: int = 0
    total: int = 0


class WSStatusMessage(BaseModel):
    type: str = "status"
    state: str = "running"  # running, completed, failed


class WSFileReadyMessage(BaseModel):
    type: str = "file_ready"
    download_url: str = ""
    filename: str = ""
