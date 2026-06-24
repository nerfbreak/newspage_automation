import streamlit as st
from datetime import datetime
from utils import check_auth, render_header, render_footer, clean_html, render_metric_card
import database

# --- AUTH CHECK ---
check_auth()

# --- HEADER ---
render_header("Automation Tool", st.session_state.current_user)

# --- DATABASE CONNECTION ---
supabase = database.init_supabase()
db_connected = supabase is not None
db_status = "CONNECTED" if db_connected else "DISCONNECTED"

# --- DATA RETRIEVAL ---
total_extractions = 0
last_extracted_dist = "N/A"
last_extracted_time = "N/A"
total_distributors = 0
total_logs = 0
audit_logs = []
dist_nodes = []

if db_connected:
    # 1. Total extractions
    try:
        res_ext = supabase.table("extraction_history").select("id", count="exact").execute()
        total_extractions = res_ext.count if res_ext.count is not None else 0
    except Exception:
        pass

    # 2. Last extraction
    try:
        res_last = supabase.table("extraction_history").select("distributor_name, created_at").order("created_at", desc=True).limit(1).execute()
        if res_last.data:
            last_extracted_dist = res_last.data[0]["distributor_name"]
            raw_time = res_last.data[0]["created_at"]
            try:
                from datetime import timezone, timedelta
                t_str = raw_time.replace("Z", "+00:00")
                dt = datetime.fromisoformat(t_str)
                # Convert UTC to local if needed, assuming GMT+7 for ID
                dt_local = dt + timedelta(hours=7)
                last_extracted_time = dt_local.strftime("%Y-%m-%d %H:%M")
            except Exception:
                last_extracted_time = raw_time[:16].replace("T", " ")
    except Exception:
        pass

    # 3. Total distributors
    try:
        res_dist = supabase.table("distributor_vault").select("id", count="exact").execute()
        total_distributors = res_dist.count if res_dist.count is not None else 0
    except Exception:
        pass

    # 4. Total Synced Logs
    try:
        res_logs = supabase.table("adjustment_logs").select("id", count="exact").execute()
        total_logs = res_logs.count if res_logs.count is not None else 0
    except Exception:
        pass

    # 5. Fetch audit logs (latest 5)
    try:
        res_audit = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(5).execute()
        audit_logs = res_audit.data if res_audit.data else []
    except Exception:
        pass

    # 6. Fetch nodes (for Network Graph)
    try:
        res_nodes = supabase.table("distributor_vault").select("nama_distributor").execute()
        dist_nodes = [r["nama_distributor"] for r in res_nodes.data] if res_nodes.data else []
    except Exception:
        pass

# --- METRIC CARDS ---
col1, col2, col3 = st.columns(3)


with col1:
    st.markdown(render_metric_card("Total Extractions", str(total_extractions)), unsafe_allow_html=True)
with col2:
    st.markdown(render_metric_card("Last Extraction", last_extracted_dist, accent=True), unsafe_allow_html=True)
with col3:
    st.markdown(render_metric_card("Registered Distributors", str(total_distributors)), unsafe_allow_html=True)

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# --- NAVIGATION HUB ---
st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>Navigation</div>", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Inventory Adjustment</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Sync real-time stock levels and reconcile inventory data with distributor files.</p>", unsafe_allow_html=True)
        if st.button("Open Inventory Adjustment", key="btn_nav_inv", width="stretch", type="primary"):
            st.switch_page("pages/1_inventory_adjustment.py")

with nav_col2:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Sales Extraction</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Run Playwright automated bots to extract distributor invoices and sync sales databases.</p>", unsafe_allow_html=True)
        if st.button("Open Sales Extraction", key="btn_nav_sales", width="stretch", type="primary"):
            st.switch_page("pages/2_sales_extraction.py")

with nav_col3:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Promotion Comparison</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Compare distributor pricing files and monitor active campaign claims.</p>", unsafe_allow_html=True)
        if st.button("Open Promotion Comparison", key="btn_nav_promo", width="stretch", type="primary"):
            st.switch_page("pages/3_promotion_comparison.py")

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

nav_col4, nav_col5, nav_col6 = st.columns(3)

with nav_col4:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Stock Mutation</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Track stock movement and mutation records across distributors.</p>", unsafe_allow_html=True)
        if st.button("Open Stock Mutation", key="btn_nav_mutation", width="stretch", type="primary"):
            st.switch_page("pages/4_stock_mutation.py")

with nav_col5:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Clearance Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Monitor and reconcile clearance inventory.</p>", unsafe_allow_html=True)
        if st.button("Open Clearance Stock", key="btn_nav_clearance", width="stretch", type="primary"):
            st.switch_page("pages/5_clearance_stock.py")

with nav_col6:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Initial Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Manage initial stock setup and baseline data.</p>", unsafe_allow_html=True)
        if st.button("Open Initial Stock", key="btn_nav_initial", width="stretch", type="primary"):
            st.switch_page("pages/6_initial_stock.py")

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# --- SYSTEM MONITORING SECTION ---
with st.container(border=False):
    st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>System Health</div>", unsafe_allow_html=True)
    
    bot_running = st.session_state.get("is_bot_running", False)
    bot_status = "RUNNING" if bot_running else "STANDBY"
    
    bot_color = "#10B981" if bot_running else "#808495"
    db_color = "#10B981" if db_connected else "#EF4444"
    
    h_col1, h_col2, h_col3 = st.columns(3)
    
    with h_col1:
        st.markdown(clean_html(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.01); min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #31333F;">Playwright Bots</span>
                <div style="display: flex; align-items: center; gap: 8px; background: {bot_color}1a; border: 1px solid {bot_color}33; padding: 4px 12px; border-radius: 20px;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {bot_color}; display: inline-block;"></span>
                    <span style="font-size: 0.68rem; font-weight: 800; color: {bot_color}; letter-spacing: 0.05em;">{bot_status}</span>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    with h_col2:
        st.markdown(clean_html(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.01); min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #31333F;">Database Connection</span>
                <div style="display: flex; align-items: center; gap: 8px; background: {db_color}1a; border: 1px solid {db_color}33; padding: 4px 12px; border-radius: 20px;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {db_color}; display: inline-block;"></span>
                    <span style="font-size: 0.68rem; font-weight: 800; color: {db_color}; letter-spacing: 0.05em;">{db_status}</span>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    with h_col3:
        st.markdown(clean_html(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; min-height: 72px; box-sizing: border-box; font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif; margin-bottom: 16px;">
                <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.6rem; font-weight: 700; color: #808495; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Last Sync</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #31333F; margin-top: 6px; line-height: 1.2;">{last_extracted_time}</div>
                </div>
                <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); display: flex; flex-direction: column; justify-content: center; text-align: right;">
                    <div style="font-size: 0.6rem; font-weight: 700; color: #808495; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Synced Logs</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #31333F; margin-top: 6px; line-height: 1.2;">{total_logs}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

render_footer()
