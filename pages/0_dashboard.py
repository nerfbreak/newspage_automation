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
        res_adj = _supabase.table("adjustment_logs").select("sku, qty, status, keterangan, np_user, created_at").order("created_at", desc=True).execute()
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

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

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

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# --- SYSTEM MONITORING SECTION ---
with st.container(border=False):
    st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>System Health</div>", unsafe_allow_html=True)
    
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

# --- OPERATIONAL ANALYTICS & ACTIVITY REPORT ---
if db_connected:
    from datetime import timezone, timedelta
    
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='box-np' style='text-align: center; margin-bottom: 20px; font-size: 1.1rem;'>Operational Analytics & Activity Report</div>", unsafe_allow_html=True)

    # Load logs for analytics
    df_adj, df_ext = load_historical_logs(supabase)

    # 1. Period Filter Selector
    col_filter, _ = st.columns([1.2, 2.8])
    with col_filter:
        period_option = st.selectbox(
            "Select Reporting Period",
            options=["Last 7 Days", "Last 30 Days", "All Time"],
            index=1,
            key="dashboard_report_period"
        )

    # Apply filters based on selected period
    now_utc = datetime.now(timezone.utc)
    if period_option == "Last 7 Days":
        cutoff_date = now_utc - timedelta(days=7)
    elif period_option == "Last 30 Days":
        cutoff_date = now_utc - timedelta(days=30)
    else:
        cutoff_date = None

    filtered_adj = df_adj.copy()
    filtered_ext = df_ext.copy()

    if cutoff_date is not None:
        if not filtered_adj.empty:
            filtered_adj = filtered_adj[filtered_adj["created_at"] >= cutoff_date]
        if not filtered_ext.empty:
            filtered_ext = filtered_ext[filtered_ext["created_at"] >= cutoff_date]

    # Calculate metrics
    sync_attempts = len(filtered_adj) if not filtered_adj.empty else 0
    extractions_run = len(filtered_ext) if not filtered_ext.empty else 0
    
    success_rate = 0.0
    if sync_attempts > 0:
        success_count = len(filtered_adj[filtered_adj["status"] == "Success"])
        success_rate = (success_count / sync_attempts) * 100

    items_adjusted = 0
    if not filtered_adj.empty:
        items_adjusted = int(filtered_adj["qty"].abs().sum())

    # 2. Render Metric Cards
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(render_metric_card("Sync Attempts", f"{sync_attempts:,}"), unsafe_allow_html=True)
    with m_col2:
        st.markdown(render_metric_card("Success Rate", f"{success_rate:.1f}%", accent=True), unsafe_allow_html=True)
    with m_col3:
        st.markdown(render_metric_card("Extractions Run", f"{extractions_run:,}"), unsafe_allow_html=True)
    with m_col4:
        st.markdown(render_metric_card("Items Adjusted", f"{items_adjusted:,}"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # 3. Trends & Charts Section
    ch_col1, ch_col2 = st.columns(2)
    
    with ch_col1:
        st.markdown("<h4 style='font-size: 0.95rem; font-weight: 700; color: #31333F; margin-bottom: 10px; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif;'>Sync Activity Trend</h4>", unsafe_allow_html=True)
        # Combine adjustments and extractions counts by date
        adj_by_date = pd.Series(dtype=int)
        ext_by_date = pd.Series(dtype=int)
        
        if not filtered_adj.empty:
            adj_by_date = filtered_adj["created_at"].dt.date.value_counts()
        if not filtered_ext.empty:
            ext_by_date = filtered_ext["created_at"].dt.date.value_counts()
            
        all_dates = sorted(list(set(adj_by_date.index) | set(ext_by_date.index)))
        if all_dates:
            df_chart = pd.DataFrame(index=all_dates)
            df_chart["SKU Adjustments"] = df_chart.index.map(adj_by_date).fillna(0).astype(int)
            df_chart["Data Extractions"] = df_chart.index.map(ext_by_date).fillna(0).astype(int)
            st.area_chart(df_chart, height=220, use_container_width=True)
        else:
            st.info("No activity logs available for the selected period.")

    with ch_col2:
        st.markdown("<h4 style='font-size: 0.95rem; font-weight: 700; color: #31333F; margin-bottom: 10px; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif;'>Adjustment Status Distribution</h4>", unsafe_allow_html=True)
        if not filtered_adj.empty:
            filtered_adj_copy = filtered_adj.copy()
            filtered_adj_copy["date"] = filtered_adj_copy["created_at"].dt.date
            status_df = filtered_adj_copy.groupby(["date", "status"]).size().unstack(fill_value=0)
            for col in ["Success", "Failed"]:
                if col not in status_df.columns:
                    status_df[col] = 0
            status_df = status_df[["Success", "Failed"]]
            st.bar_chart(status_df, height=220, use_container_width=True, color=["#10B981", "#EF4444"])
        else:
            st.info("No sync operations recorded in this period.")

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    # 4. Recent Execution Logs (Tabs)
    import html
    st.markdown("<h4 style='font-size: 1rem; font-weight: 700; color: #31333F; margin-bottom: 10px; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif;'>Recent Execution Records</h4>", unsafe_allow_html=True)
    tab_adj, tab_ext = st.tabs(["Recent SKU Adjustments", "Recent Data Extractions"])
    
    with tab_adj:
        if not df_adj.empty:
            recent_adj = df_adj.head(15).copy()
            recent_adj["time_local"] = recent_adj["created_at"].dt.tz_convert('Asia/Jakarta').dt.strftime("%Y-%m-%d %H:%M:%S")
            
            table_rows = ""
            for _, row in recent_adj.iterrows():
                status_color = "#10B981" if row["status"] == "Success" else "#EF4444"
                status_bg = "rgba(16, 185, 129, 0.1)" if row["status"] == "Success" else "rgba(239, 68, 68, 0.1)"
                status_badge = f"<span style='background-color: {status_bg}; color: {status_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid {status_color}33;'>{row['status'].upper()}</span>"
                
                qty_val = int(row['qty'])
                qty_str = f"+{qty_val:,}" if qty_val > 0 else f"{qty_val:,}"
                qty_color = "#09A53C" if qty_val > 0 else ("#FF2B2B" if qty_val < 0 else "#31333F")
                qty_badge = f"<span style='color: {qty_color}; font-weight: 600;'>{qty_str}</span>"
                
                table_rows += f"""
                <tr>
                    <td style='white-space: nowrap;'>{row['time_local']}</td>
                    <td><code>{html.escape(str(row['sku']))}</code></td>
                    <td>{qty_badge}</td>
                    <td style='text-align: center;'>{status_badge}</td>
                    <td>{html.escape(str(row['keterangan']))}</td>
                    <td><code>{html.escape(str(row['np_user']))}</code></td>
                </tr>
                """
                
            table_html = f"""
            <div class='table-container'>
                <table class='custom-table'>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>SKU Code</th>
                            <th>Quantity</th>
                            <th style='text-align: center;'>Status</th>
                            <th>Keterangan</th>
                            <th>Operator</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("No adjustment logs recorded yet.")
            
    with tab_ext:
        if not df_ext.empty:
            recent_ext = df_ext.head(15).copy()
            recent_ext["time_local"] = recent_ext["created_at"].dt.tz_convert('Asia/Jakarta').dt.strftime("%Y-%m-%d %H:%M:%S")
            
            table_rows = ""
            for _, row in recent_ext.iterrows():
                status_color = "#10B981" if row["status"] == "Success" else "#EF4444"
                status_bg = "rgba(16, 185, 129, 0.1)" if row["status"] == "Success" else "rgba(239, 68, 68, 0.1)"
                status_badge = f"<span style='background-color: {status_bg}; color: {status_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid {status_color}33;'>{row['status'].upper()}</span>"
                
                table_rows += f"""
                <tr>
                    <td style='white-space: nowrap;'>{row['time_local']}</td>
                    <td>{html.escape(str(row['distributor_name']))}</td>
                    <td style='text-align: center;'>{status_badge}</td>
                    <td><code>{html.escape(str(row['extracted_by']))}</code></td>
                </tr>
                """
                
            table_html = f"""
            <div class='table-container'>
                <table class='custom-table'>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Distributor</th>
                            <th style='text-align: center;'>Status</th>
                            <th>Run By</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("No extraction history logs recorded yet.")

render_footer()
