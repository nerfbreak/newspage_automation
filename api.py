import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import pandas as pd
import datetime

# Optimize modules
import database
import playwright_engine
from utils import send_telegram_alert

app = FastAPI(
    title="Optimize Newspage Headless API",
    description="API for triggering extraction and execution tasks",
    version="1.0"
)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# Initialize database
supabase = database.init_supabase_direct()
sys_cfg = database.get_system_config(supabase)
URL_LOGIN = sys_cfg.get("URL_LOGIN", "")
TIMEOUT_MS = sys_cfg.get("TIMEOUT_MS", 60000)
TABLE_UPDATE_INTERVAL = sys_cfg.get("TABLE_UPDATE_INTERVAL", 5)

# ---------------------------------------------------------
# DUMMY CLASSES FOR STREAMLIT UI CALLBACKS
# ---------------------------------------------------------
class DummyPlaceholder:
    def markdown(self, *args, **kwargs): pass
    def empty(self, *args, **kwargs): pass
    def dataframe(self, *args, **kwargs): pass
    def caption(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def button(self, *args, **kwargs): return False
    
def dummy_ui_log(module: str, msg: str):
    logger.info(f"[{module}] {msg}")

def dummy_alert_callback(msg: str):
    logger.warning(f"ALERT: {msg}")
    send_telegram_alert(msg)

# ---------------------------------------------------------
# PYDANTIC MODELS
# ---------------------------------------------------------
class ExtractRequest(BaseModel):
    distributor_name: str
    warehouse: Optional[str] = None
    requested_by: Optional[str] = "API_USER"

class AdjustmentItem(BaseModel):
    SKU: str
    Qty: int
    Reason: Optional[str] = None

class ExecutionRequest(BaseModel):
    distributor_name: str
    warehouse: Optional[str] = None
    items: List[AdjustmentItem]
    requested_by: Optional[str] = "API_USER"

# ---------------------------------------------------------
# BACKGROUND TASK WRAPPERS
# ---------------------------------------------------------
def bg_task_extract(req: ExtractRequest):
    bot_user, bot_pass = database.get_distributor_creds(supabase, req.distributor_name)
    if not bot_user:
        logger.error(f"Credentials not found for {req.distributor_name}")
        return

    # Determine warehouse
    whs_exceptions = database.get_distributor_warehouse_exceptions(supabase)
    whs = req.warehouse or whs_exceptions.get(req.distributor_name, whs_exceptions.get(bot_user, sys_cfg.get("WAREHOUSE", "")))

    logger.info(f"Starting extraction for {req.distributor_name} at {whs}")
    
    # Run the playwright engine
    try:
        # Note: In headless API, st.session_state is not available natively if playwright_engine calls it directly.
        # But we pass the arguments it asks for. If playwright_engine uses `import streamlit as st` and writes to `st.session_state`
        # outside of a Streamlit context, it may throw an error. In a true headless environment, engine needs to be decoupled from Streamlit.
        playwright_engine.run_extract(
            user_id_np=bot_user,
            pass_np=bot_pass,
            selected_distributor=req.distributor_name,
            URL_LOGIN=URL_LOGIN,
            TIMEOUT_MS=TIMEOUT_MS,
            WAREHOUSE=whs,
            ext_ui_log=dummy_ui_log,
            alert_callback=dummy_alert_callback,
            supabase=supabase,
            current_user=req.requested_by
        )
        logger.info(f"Extraction completed for {req.distributor_name}")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")


def bg_task_execute(req: ExecutionRequest):
    bot_user, bot_pass = database.get_distributor_creds(supabase, req.distributor_name)
    if not bot_user:
        logger.error(f"Credentials not found for {req.distributor_name}")
        return

    # Determine warehouse
    whs_exceptions = database.get_distributor_warehouse_exceptions(supabase)
    whs = req.warehouse or whs_exceptions.get(req.distributor_name, whs_exceptions.get(bot_user, sys_cfg.get("WAREHOUSE", "")))

    # Convert items to DataFrame
    data = []
    for item in req.items:
        data.append({"SKU": item.SKU, "Qty": item.Qty})
    df_view = pd.DataFrame(data)

    logger.info(f"Starting execution for {req.distributor_name} at {whs} with {len(df_view)} items")
    
    try:
        playwright_engine.run_execution_manual(
            df_view=df_view,
            bot_user=bot_user,
            bot_pass=bot_pass,
            selected_distributor=req.distributor_name,
            URL_LOGIN=URL_LOGIN,
            TIMEOUT_MS=TIMEOUT_MS,
            WAREHOUSE=whs,
            REASON_CODE=sys_cfg.get("REASON_CODE", "SA2"),
            TABLE_UPDATE_INTERVAL=TABLE_UPDATE_INTERVAL,
            ui_log=dummy_ui_log,
            alert_callback=dummy_alert_callback,
            table_placeholder=DummyPlaceholder(),
            log_label_placeholder=DummyPlaceholder(),
            supabase=supabase
        )
        logger.info(f"Execution completed for {req.distributor_name}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")

# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "time": datetime.datetime.now().isoformat()}

@app.post("/api/v1/extract")
def trigger_extract(req: ExtractRequest, bg_tasks: BackgroundTasks):
    """
    Triggers a background extraction job for the given distributor.
    """
    bg_tasks.add_task(bg_task_extract, req)
    return {"status": "queued", "message": f"Extraction job for {req.distributor_name} added to background queue."}

@app.post("/api/v1/execute")
def trigger_execute(req: ExecutionRequest, bg_tasks: BackgroundTasks):
    """
    Triggers a background execution job for manual adjustment items.
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="Items list cannot be empty")
    
    bg_tasks.add_task(bg_task_execute, req)
    return {"status": "queued", "message": f"Execution job for {req.distributor_name} added to background queue."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
