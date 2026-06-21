import html
import streamlit as st
from datetime import datetime, timedelta
from utils import check_auth, render_header, render_footer
from utils.theme import load_theme
import database

# --- AUTH CHECK ---
check_auth()

# --- Load Theme (in case page is accessed directly) ---
load_theme()

# --- HEADER ---
render_header("Automation Tool", st.session_state.current_user)

# --- DATABASE CONNECTION ---
supabase = database.init_supabase()
db_connected = supabase is not None
db_status = "CONNECTED" if db_connected else "DISCONNECTED"

# --- CACHED DATA QUERIES (60s TTL) ---
@st.cache_data(ttl=60, show_spinner=False)
def fetch_total_extractions(_supabase):
    try:
        res = _supabase.table("extraction_history").select("id", count="exact").execute()
        return res.count if res.count is not None else 0
    except Exception:
        return 0

@st.cache_data(ttl=60, show_spinner=False)
def fetch_last_extraction(_supabase):
    try:
        res = _supabase.table("extraction_history").select("distributor_name, created_at").order("created_at", desc=True).limit(1).execute()
        if res.data:
            dist_name = res.data[0]["distributor_name"]
            raw_time = res.data[0]["created_at"]
            try:
                from datetime import timezone, timedelta
                t_str = raw_time.replace("Z", "+00:00")
                dt = datetime.fromisoformat(t_str)
                dt_local = dt + timedelta(hours=7)
                time_str = dt_local.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = raw_time[:16].replace("T", " ")
            return dist_name, time_str
    except Exception:
        pass
    return "N/A", "N/A"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_total_distributors(_supabase):
    try:
        res = _supabase.table("distributor_vault").select("id", count="exact").execute()
        return res.count if res.count is not None else 0
    except Exception:
        return 0

@st.cache_data(ttl=60, show_spinner=False)
def fetch_total_logs(_supabase):
    try:
        res = _supabase.table("adjustment_logs").select("id", count="exact").execute()
        return res.count if res.count is not None else 0
    except Exception:
        return 0

@st.cache_data(ttl=60, show_spinner=False)
def fetch_audit_logs(_supabase):
    try:
        res = _supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(5).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- DATA RETRIEVAL ---
total_extractions = 0
last_extracted_dist = "N/A"
last_extracted_time = "N/A"
total_distributors = 0
total_logs = 0
audit_logs = []
dist_nodes = []

if db_connected:
    total_extractions = fetch_total_extractions(supabase)
    last_extracted_dist, last_extracted_time = fetch_last_extraction(supabase)
    total_distributors = fetch_total_distributors(supabase)
    total_logs = fetch_total_logs(supabase)
    audit_logs = fetch_audit_logs(supabase)

# ============================================================
# METRIC CARDS (native Streamlit)
# ============================================================
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown(":material/cloud_download: **Total Extractions**")
        st.markdown(f"### {total_extractions}")

with col2:
    with st.container(border=True):
        st.markdown(":material/schedule: **Last Extraction**", help="Most recent data extraction")
        st.markdown(f"### {last_extracted_dist}")
        st.caption(last_extracted_time)

with col3:
    with st.container(border=True):
        st.markdown(":material/store: **Registered Distributors**")
        st.markdown(f"### {total_distributors}")

st.space("medium")

# ============================================================
# NAVIGATION HUB (native Streamlit)
# ============================================================
st.markdown("#### :material/dashboard: Navigation")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown("##### :material/inventory_2: Inventory Adjustment")
        st.caption("Sync real-time stock levels and reconcile inventory data with distributor files.")
        st.space("small")
        if st.button("Open", key="btn_nav_inv", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/1_inventory_adjustment.py")

with nav_col2:
    with st.container(border=True):
        st.markdown("##### :material/receipt_long: Sales Extraction")
        st.caption("Run Playwright automated bots to extract distributor invoices and sync sales databases.")
        st.space("small")
        if st.button("Open", key="btn_nav_sales", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/2_sales_extraction.py")

with nav_col3:
    with st.container(border=True):
        st.markdown("##### :material/compare: Promotion Comparison")
        st.caption("Compare distributor pricing files and monitor active campaign claims.")
        st.space("small")
        if st.button("Open", key="btn_nav_promo", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/3_promotion_comparison.py")

st.space("medium")

nav_col4, nav_col5, nav_col6 = st.columns(3)

with nav_col4:
    with st.container(border=True):
        st.markdown("##### :material/swap_horiz: Mutasi Stock")
        st.caption("Transfer stock between distributors. Deduct from sender and add to receiver in parallel.")
        st.space("small")
        if st.button("Open", key="btn_nav_mutasi", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/4_stock_mutation.py")

with nav_col5:
    with st.container(border=True):
        st.markdown("##### :material/delete_sweep: Clearance Stock")
        st.caption("Extract and clear all distributor stock to zero via automated Playwright adjustments.")
        st.space("small")
        if st.button("Open", key="btn_nav_clearance", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/5_clearance_stock.py")

with nav_col6:
    with st.container(border=True):
        st.markdown("##### :material/upload_file: Initial Stock")
        st.caption("Upload stock file and populate empty distributor inventory via automated Playwright adjustments.")
        st.space("small")
        if st.button("Open", key="btn_nav_init_stock", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/6_initial_stock.py")

st.space("medium")

# ============================================================
# SYSTEM HEALTH (native Streamlit)
# ============================================================
st.markdown("#### :material/monitoring: System Health")

bot_running = st.session_state.get("is_bot_running", False)
bot_status = "RUNNING" if bot_running else "STANDBY"

h_col1, h_col2, h_col3 = st.columns(3)

with h_col1:
    with st.container(border=True):
        st.markdown(":material/smart_toy: **Playwright Bots**")
        if bot_running:
            st.badge("RUNNING", color="green")
        else:
            st.badge("STANDBY", color="gray")

with h_col2:
    with st.container(border=True):
        st.markdown(":material/database: **Database**")
        if db_connected:
            st.badge("CONNECTED", color="green")
        else:
            st.badge("DISCONNECTED", color="red")

with h_col3:
    with st.container(border=True):
        st.markdown(":material/sync: **Last Sync**")
        st.markdown(f"**{last_extracted_time}**")
        st.caption(f"{total_logs} synced logs")

st.space("medium")

# ============================================================
# AUDIT LOG TIMELINE (native Streamlit)
# ============================================================
if audit_logs:
    st.markdown("#### :material/history: Recent Activity")

    for i, log in enumerate(audit_logs):
        action = html.escape(log.get("action", "unknown"))
        user = html.escape(log.get("user_name", "system"))
        raw_ts = log.get("created_at", "")
        details = html.escape(log.get("details", ""))

        # Parse timestamp
        try:
            t_str = raw_ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(t_str)
            dt_local = dt + timedelta(hours=7)
            time_display = dt_local.strftime("%H:%M %d/%m")
        except Exception:
            time_display = raw_ts[:16].replace("T", " ") if raw_ts else "N/A"

        # Icon & color by action type
        if "login" in action.lower():
            icon, color = "login", "blue"
        elif "extract" in action.lower():
            icon, color = "cloud_download", "green"
        elif "error" in action.lower() or "fail" in action.lower():
            icon, color = "error", "red"
        elif "adjust" in action.lower() or "execute" in action.lower():
            icon, color = "build", "orange"
        else:
            icon, color = "info", "gray"

        with st.container(border=True):
            ic, tc, mc = st.columns([0.05, 0.7, 0.25], vertical_alignment="center")
            with ic:
                st.markdown(f":material/{icon}:")
            with tc:
                st.markdown(f"**{action}**")
                if details:
                    st.caption(details)
            with mc:
                st.caption(user)
                st.caption(time_display)

render_footer()
