import html
import streamlit as st
from datetime import datetime
from utils import check_auth, render_header, render_footer, clean_html
import database

# --- Material Icon helper (works inside unsafe_allow_html) ---
def mi(name, size="1em"):
    return f'<span class="material-symbols-outlined" style="font-size:{size}">{name}</span>'

# --- AUTH CHECK ---
check_auth()

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

# --- METRIC CARDS ---
col1, col2, col3 = st.columns(3)

def render_metric_card(title, value, icon="", accent=False):
    # Styling variables to match Streamlit Design System theme
    bg = "#3b82f6" if accent else "#262626"
    fg = "#ffffff" if accent else "#e5e5e5"
    border = "1px solid rgba(59, 130, 246, 0.3)" if accent else "1px solid #404040"
    shadow = "0 4px 16px rgba(59, 130, 246, 0.2)" if accent else "0 4px 12px rgba(0, 0, 0, 0.3)"
    label_color = "rgba(255, 255, 255, 0.7)" if accent else "#a3a3a3"
    icon_html = f'<span class="material-symbols-outlined" style="font-size: 14px; margin-right: 6px; vertical-align: middle;">{icon}</span>' if icon else ''
    
    # Dynamic font sizing and centering calculations
    if len(value) > 20:
        font_size_px = 18
    elif len(value) > 10:
        font_size_px = 24
    else:
        font_size_px = 38
        
    font_size = f"{font_size_px}px"
    
    # Calculate margin-top to align the visual centers of the texts to exactly 70px from top
    target_center = 70
    margin_top = int((target_center - font_size_px / 2) - 31)
    
    return clean_html(f"""
    <div style='
        background-color: {bg};
        color: {fg};
        border: {border};
        border-radius: 10px;
        padding: 20px 24px;
        width: 100%;
        height: 125px;
        box-sizing: border-box;
        font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
        margin-bottom: 16px;
        box-shadow: {shadow};
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    '>
        <div style='font-size: 11px; font-weight: 600; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; height: 11px; line-height: 1;'>{icon_html}{title}</div>
        <div style='font-size: {font_size}; font-weight: 700; color: {fg}; margin-top: {margin_top}px; line-height: 1;'>{value}</div>
    </div>
    """)

with col1:
    st.markdown(render_metric_card("Total Extractions", str(total_extractions), icon="cloud_download"), unsafe_allow_html=True)
with col2:
    st.markdown(render_metric_card("Last Extraction", last_extracted_dist, icon="schedule", accent=True), unsafe_allow_html=True)
with col3:
    st.markdown(render_metric_card("Registered Distributors", str(total_distributors), icon="store"), unsafe_allow_html=True)

st.space("medium")

# --- NAVIGATION HUB ---
st.markdown(f"<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>{mi('dashboard')} &nbsp;Navigation</div>", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('inventory_2')} &nbsp;Inventory Adjustment</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Sync real-time stock levels and reconcile inventory data with distributor files.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_inv", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/1_inventory_adjustment.py")

with nav_col2:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('receipt_long')} &nbsp;Sales Extraction</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Run Playwright automated bots to extract distributor invoices and sync sales databases.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_sales", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/2_sales_extraction.py")

with nav_col3:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('compare')} &nbsp;Promotion Comparison</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Compare distributor pricing files and monitor active campaign claims.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_promo", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/3_promotion_comparison.py")

st.space("medium")

# --- NAVIGATION ROW 2 ---
nav_col4, nav_col5, nav_col6 = st.columns(3)

with nav_col4:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('swap_horiz')} &nbsp;Mutasi Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Transfer stock between distributors. Deduct from sender and add to receiver in parallel.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_mutasi", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/4_stock_mutation.py")

with nav_col5:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('delete_sweep')} &nbsp;Clearance Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Extract and clear all distributor stock to zero via automated Playwright adjustments.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_clearance", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/5_clearance_stock.py")

with nav_col6:
    with st.container(border=True):
        st.markdown(f"<h4 style='margin-top: 0px; font-weight: 700; color: #e5e5e5; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>{mi('upload_file')} &nbsp;Initial Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #a3a3a3; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Upload stock file and populate empty distributor inventory via automated Playwright adjustments.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_init_stock", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/6_initial_stock.py")

st.space("medium")

# --- SYSTEM MONITORING SECTION ---
with st.container(border=False):
    st.markdown(f"<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>{mi('monitoring')} &nbsp;System Health</div>", unsafe_allow_html=True)
    
    bot_running = st.session_state.get("is_bot_running", False)
    bot_status = "RUNNING" if bot_running else "STANDBY"
    
    bot_color = "#22C55E" if bot_running else "#a3a3a3"
    db_color = "#22C55E" if db_connected else "#ef4444"
    
    h_col1, h_col2, h_col3 = st.columns(3)
    
    with h_col1:
        st.markdown(clean_html(f"""
            <div style="background-color: #1e1e1e; border: 1px solid #333333; border-radius: 10px; padding: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.2); min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #e5e5e5;">{mi('smart_toy')} Playwright Bots</span>
                <div style="display: flex; align-items: center; gap: 8px; background: {bot_color}1a; border: 1px solid {bot_color}33; padding: 4px 12px; border-radius: 20px;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {bot_color}; display: inline-block;"></span>
                    <span style="font-size: 0.68rem; font-weight: 800; color: {bot_color}; letter-spacing: 0.05em;">{bot_status}</span>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    with h_col2:
        st.markdown(clean_html(f"""
            <div style="background-color: #1e1e1e; border: 1px solid #333333; border-radius: 10px; padding: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.2); min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #e5e5e5;">{mi('database')} Database</span>
                <div style="display: flex; align-items: center; gap: 8px; background: {db_color}1a; border: 1px solid {db_color}33; padding: 4px 12px; border-radius: 20px;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {db_color}; display: inline-block;"></span>
                    <span style="font-size: 0.68rem; font-weight: 800; color: {db_color}; letter-spacing: 0.05em;">{db_status}</span>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    with h_col3:
        st.markdown(clean_html(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <div style="background-color: #1e1e1e; border: 1px solid #333333; border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.6rem; font-weight: 700; color: #a3a3a3; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Last Sync</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #e5e5e5; margin-top: 6px; line-height: 1.2;">{last_extracted_time}</div>
                </div>
                <div style="background-color: #1e1e1e; border: 1px solid #333333; border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: center; text-align: right;">
                    <div style="font-size: 0.6rem; font-weight: 700; color: #a3a3a3; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Synced Logs</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #e5e5e5; margin-top: 6px; line-height: 1.2;">{total_logs}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

st.space("medium")

# --- AUDIT LOG TIMELINE ---
if audit_logs:
    st.markdown(f"<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>{mi('history')} &nbsp;Recent Activity</div>", unsafe_allow_html=True)
    
    for log in audit_logs:
        action = html.escape(log.get("action", "unknown"))
        user = html.escape(log.get("user_name", "system"))
        raw_ts = log.get("created_at", "")
        details = html.escape(log.get("details", ""))
        
        # Parse timestamp
        try:
            from datetime import timedelta
            t_str = raw_ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(t_str)
            dt_local = dt + timedelta(hours=7)
            time_display = dt_local.strftime("%H:%M %d/%m")
        except Exception:
            time_display = raw_ts[:16].replace("T", " ") if raw_ts else "N/A"
        
        # Color code by action type
        if "login" in action.lower():
            icon = "login"
            accent = "#3b82f6"
        elif "extract" in action.lower():
            icon = "cloud_download"
            accent = "#22c55e"
        elif "error" in action.lower() or "fail" in action.lower():
            icon = "error"
            accent = "#ef4444"
        elif "adjust" in action.lower() or "execute" in action.lower():
            icon = "build"
            accent = "#f97316"
        else:
            icon = "info"
            accent = "#a3a3a3"
        
        detail_html = f'<span style="color: #737373; font-size: 0.72rem; margin-left: 8px;">{details}</span>' if details else ''
        st.markdown(clean_html(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-left: 3px solid {accent}; background: #1e1e1e; border-radius: 0 8px 8px 0; margin-bottom: 8px; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif;">
                <span style="font-size: 1.2rem;">{mi(icon)}</span>
                <div style="flex: 1;">
                    <span style="font-size: 0.82rem; font-weight: 600; color: #e5e5e5;">{action}</span>
                    {detail_html}
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.65rem; color: #a3a3a3;">{user}</div>
                    <div style="font-size: 0.6rem; color: #737373;">{time_display}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

render_footer()
