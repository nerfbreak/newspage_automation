import streamlit as st
from datetime import datetime
import pandas as pd
from utils import check_auth, render_header, render_footer, clean_html, render_metric_card
import database

@st.cache_data(ttl=60)
def load_historical_logs(_supabase):
    df_adj = pd.DataFrame()
    df_ext = pd.DataFrame()
    if not _supabase:
        return df_adj, df_ext
    
    try:
        res_adj = _supabase.table("adjustment_logs").select("sku, qty, status, keterangan, np_user, run_by, created_at").order("created_at", desc=True).execute()
        if res_adj.data:
            df_adj = pd.DataFrame(res_adj.data)
            df_adj["created_at"] = pd.to_datetime(df_adj["created_at"])
    except Exception as e:
        st.error(f"Error loading adjustment logs: {e}")
        
    try:
        res_ext = _supabase.table("extraction_history").select("distributor_name, status, extracted_by, created_at").order("created_at", desc=True).execute()
        if res_ext.data:
            df_ext = pd.DataFrame(res_ext.data)
            df_ext["created_at"] = pd.to_datetime(df_ext["created_at"])
    except Exception as e:
        st.error(f"Error loading extraction history: {e}")

    return df_adj, df_ext

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
user_to_dist = {}

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

    # 6. Fetch nodes (for Network Graph) and distributor mapping
    try:
        res_nodes = supabase.table("distributor_vault").select("np_user_id, nama_distributor").execute()
        dist_nodes = [r["nama_distributor"] for r in res_nodes.data] if res_nodes.data else []
        user_to_dist = {r["np_user_id"]: r["nama_distributor"] for r in res_nodes.data if r.get("np_user_id")}
    except Exception:
        pass


# --- HERO SECTION: SYSTEM HEALTH & METRICS ---
st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>System Health & Overview</div>", unsafe_allow_html=True)

bot_running = (
    st.session_state.get("is_bot_running", False) or
    st.session_state.get("is_promo_bot_running", False) or
    st.session_state.get("is_mutasi_running", False) or
    st.session_state.get("is_clearance_running", False) or
    st.session_state.get("is_initial_running", False)
)
bot_status = "RUNNING" if bot_running else "STANDBY"
bot_color = "#10B981" if bot_running else "#808495"
db_color = "#10B981" if db_connected else "#EF4444"

# 4 Columns for System Health
h_col1, h_col2, h_col3, h_col4 = st.columns(4)

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
            <span style="font-size: 0.85rem; font-weight: 600; color: #31333F;">DB Connection</span>
            <div style="display: flex; align-items: center; gap: 8px; background: {db_color}1a; border: 1px solid {db_color}33; padding: 4px 12px; border-radius: 20px;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {db_color}; display: inline-block;"></span>
                <span style="font-size: 0.68rem; font-weight: 800; color: {db_color}; letter-spacing: 0.05em;">{db_status}</span>
            </div>
        </div>
    """), unsafe_allow_html=True)

with h_col3:
    st.markdown(clean_html(f"""
        <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); display: flex; flex-direction: column; justify-content: center; min-height: 72px; margin-bottom: 16px;">
            <div style="font-size: 0.6rem; font-weight: 700; color: #808495; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Total Extractions</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #31333F; margin-top: 6px; line-height: 1.2;">{total_extractions}</div>
        </div>
    """), unsafe_allow_html=True)

with h_col4:
    st.markdown(clean_html(f"""
        <div style="background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); display: flex; flex-direction: column; justify-content: center; min-height: 72px; margin-bottom: 16px;">
            <div style="font-size: 0.6rem; font-weight: 700; color: #808495; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">Total Logs / Reg. Dist.</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #31333F; margin-top: 6px; line-height: 1.2;">{total_logs} / {total_distributors}</div>
        </div>
    """), unsafe_allow_html=True)

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)


# --- NAVIGATION HUB ---
st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>App Launcher</div>", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Inventory Adjustment</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Sync real-time stock levels and reconcile inventory data with distributor files.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_inv", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/1_inventory_adjustment.py")

with nav_col2:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Sales Extraction</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Run Playwright automated bots to extract distributor invoices and sync sales databases.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_sales", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/2_sales_extraction.py")

with nav_col3:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Promotion Comparison</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Compare distributor pricing files and monitor active campaign claims.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_promo", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/3_promotion_comparison.py")

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

nav_col4, nav_col5, nav_col6 = st.columns(3)

with nav_col4:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Stock Mutation</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Track stock movement and mutation records across distributors.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_mutation", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/4_stock_mutation.py")

with nav_col5:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Clearance Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Monitor and reconcile clearance inventory.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_clearance", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/5_clearance_stock.py")

with nav_col6:
    with st.container(border=True):
        st.markdown("<h4 style='margin-top: 0px; font-weight: 700; color: #31333F; font-size: 1.1rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; letter-spacing: -0.01em;'>Initial Stock</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #808495; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; line-height: 1.5; min-height: 60px; margin-bottom: 18px;'>Manage initial stock setup and baseline data.</p>", unsafe_allow_html=True)
        if st.button("Open", key="btn_nav_initial", width="stretch", type="primary", icon=":material/open_in_new:"):
            st.switch_page("pages/6_initial_stock.py")

# --- ACTIVITY REPORT ---
if db_connected:
    from datetime import timezone, timedelta
    import html
    
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>Activity Report</div>", unsafe_allow_html=True)

    # Load logs
    df_adj, df_ext = load_historical_logs(supabase)

    # Period Filter
    col_filter, _ = st.columns([1.2, 2.8])
    with col_filter:
        period_option = st.selectbox(
            "Select Reporting Period",
            options=["Today", "Last 7 Days", "Last 30 Days", "All Time"],
            index=2,
            key="dashboard_report_period"
        )

    now_utc = datetime.now(timezone.utc)
    if period_option == "Today":
        cutoff_date = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_option == "Last 7 Days":
        cutoff_date = now_utc - timedelta(days=7)
    elif period_option == "Last 30 Days":
        cutoff_date = now_utc - timedelta(days=30)
    else:
        cutoff_date = None

    # Build unified activity log from both tables
    unified_rows = []

    if not df_adj.empty:
        filtered_adj = df_adj.copy()
        if cutoff_date is not None:
            filtered_adj = filtered_adj[filtered_adj["created_at"] >= cutoff_date]
        for _, row in filtered_adj.iterrows():
            qty_str = str(row.get("qty", ""))
            # Distinguish module: Stock Mutation logs qty as "PAC:x CAR:x EA:x"
            if "PAC:" in qty_str or "CAR:" in qty_str:
                module_name = "Stock Mutation"
            else:
                module_name = "Inventory Adjustment"
            distributor = user_to_dist.get(row.get("np_user", ""), row.get("np_user", "N/A"))
            run_by_val = row.get("run_by") or row.get("np_user", "N/A")

            unified_rows.append({
                "timestamp": row["created_at"],
                "distributor": distributor,
                "module": module_name,
                "status": row.get("status", "N/A"),
                "run_by": run_by_val,
            })

    if not df_ext.empty:
        filtered_ext = df_ext.copy()
        if cutoff_date is not None:
            filtered_ext = filtered_ext[filtered_ext["created_at"] >= cutoff_date]
        for _, row in filtered_ext.iterrows():
            unified_rows.append({
                "timestamp": row["created_at"],
                "distributor": row.get("distributor_name", "N/A"),
                "module": "Sales Extraction",
                "status": row.get("status", "N/A"),
                "run_by": row.get("extracted_by", "N/A"),
            })

    # Sort by timestamp descending and limit to latest 30 entries
    unified_rows.sort(key=lambda x: x["timestamp"], reverse=True)
    unified_rows = unified_rows[:30]

    # Render unified table
    st.markdown("<h4 style='font-size: 1rem; font-weight: 700; color: #31333F; margin-bottom: 10px; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif;'>Log History</h4>", unsafe_allow_html=True)

    if unified_rows:
        table_rows_html = ""
        for entry in unified_rows:
            # Timestamp - convert to local
            try:
                ts = entry["timestamp"]
                if ts.tzinfo is not None:
                    ts_str = ts.tz_convert('Asia/Jakarta').strftime("%Y-%m-%d %H:%M:%S")
                else:
                    ts_str = (ts + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_str = str(entry["timestamp"])[:19]

            # Status badge
            status_val = str(entry["status"])
            if status_val == "Success":
                s_color, s_bg = "#10B981", "rgba(16, 185, 129, 0.1)"
            elif status_val in ("Failed", "Invalid"):
                s_color, s_bg = "#EF4444", "rgba(239, 68, 68, 0.1)"
            else:
                s_color, s_bg = "#F59E0B", "rgba(245, 158, 11, 0.1)"
            status_badge = f"<span style='display: inline-block; white-space: nowrap; background-color: {s_bg}; color: {s_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid {s_color}33;'>{html.escape(status_val.upper())}</span>"

            # Module badge with color coding
            mod = entry["module"]
            mod_colors = {
                "Inventory Adjustment": ("#0068C9", "rgba(0, 104, 201, 0.08)"),
                "Sales Extraction": ("#7C3AED", "rgba(124, 58, 237, 0.08)"),
                "Stock Mutation": ("#D97706", "rgba(217, 119, 6, 0.08)"),
                "Promotion Comparison": ("#059669", "rgba(5, 150, 105, 0.08)"),
                "Clearance Stock": ("#DC2626", "rgba(220, 38, 38, 0.08)"),
                "Initial Stock": ("#6366F1", "rgba(99, 102, 241, 0.08)"),
            }
            m_color, m_bg = mod_colors.get(mod, ("#808495", "rgba(128, 132, 149, 0.08)"))
            module_badge = f"<span style='display: inline-block; white-space: nowrap; background-color: {m_bg}; color: {m_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; border: 1px solid {m_color}33;'>{html.escape(mod)}</span>"

            table_rows_html += f"""
            <tr>
                <td style='white-space: nowrap;'>{ts_str}</td>
                <td>{html.escape(str(entry['distributor']))}</td>
                <td>{module_badge}</td>
                <td style='text-align: center;'>{status_badge}</td>
                <td><code>{html.escape(str(entry['run_by']))}</code></td>
            </tr>
            """

        table_html = f"""
        <div class='table-container'>
            <table class='custom-table'>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Distributor</th>
                        <th>Module</th>
                        <th style='text-align: center;'>Status</th>
                        <th>Run By</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
        </div>
        """
        st.markdown(clean_html(table_html), unsafe_allow_html=True)
    else:
        st.info("No execution records found for the selected period.")

render_footer()
