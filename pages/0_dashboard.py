import streamlit as st
from datetime import datetime
import pandas as pd
import html
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
# We keep the original render_header for session state and top border logic
render_header("Automation Tool", st.session_state.current_user)

# --- DATABASE CONNECTION ---
supabase = database.init_supabase()
db_connected = supabase is not None

# --- DATA RETRIEVAL ---
total_extractions = 0
total_distributors = 0
total_logs = 0
user_to_dist = {}

if db_connected:
    try:
        res_ext = supabase.table("extraction_history").select("id", count="exact").execute()
        total_extractions = res_ext.count if res_ext.count is not None else 0
    except: pass
    try:
        res_dist = supabase.table("distributor_vault").select("id", count="exact").execute()
        total_distributors = res_dist.count if res_dist.count is not None else 0
    except: pass
    try:
        res_logs = supabase.table("adjustment_logs").select("id", count="exact").execute()
        total_logs = res_logs.count if res_logs.count is not None else 0
    except: pass
    try:
        res_nodes = supabase.table("distributor_vault").select("np_user_id, nama_distributor").execute()
        user_to_dist = {r["np_user_id"]: r["nama_distributor"] for r in res_nodes.data if r.get("np_user_id")}
    except: pass

bot_running = (
    st.session_state.get("is_bot_running", False) or
    st.session_state.get("is_promo_bot_running", False) or
    st.session_state.get("is_mutasi_running", False) or
    st.session_state.get("is_clearance_running", False) or
    st.session_state.get("is_initial_running", False)
)

# --- HERO BANNER ---
st.markdown(f"""
<div style='margin-bottom: 24px;'>
    <h1 style='font-size: 2.2rem; font-weight: 800; color: #0F172A; margin: 0;'>Halo, {html.escape(st.session_state.current_user)}! 👋</h1>
    <p style='font-size: 0.95rem; color: #64748B; margin-top: 4px; font-weight: 500;'>Pantau ringkasan aktivitas otomatisasi distributor Anda hari ini, {datetime.now().strftime('%d %b %Y')}.</p>
</div>
""", unsafe_allow_html=True)

# --- TOP KPI METRICS ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); min-height: 98px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 16px;'>
            <div style='color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>Total Extractions</div>
            <div style='color: #0F172A; font-size: 1.8rem; font-weight: 800; margin-top: 4px; line-height: 1;'>{total_extractions}</div>
        </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); min-height: 98px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 16px;'>
            <div style='color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>Active Distributors</div>
            <div style='color: #0F172A; font-size: 1.8rem; font-weight: 800; margin-top: 4px; line-height: 1;'>{total_distributors}</div>
        </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); min-height: 98px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 16px;'>
            <div style='color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>Synced Logs</div>
            <div style='color: #0F172A; font-size: 1.8rem; font-weight: 800; margin-top: 4px; line-height: 1;'>{total_logs}</div>
        </div>
    """, unsafe_allow_html=True)
with m4:
    bot_class = "status-dot-green" if bot_running else "status-dot-gray"
    bot_text = "BOT RUNNING" if bot_running else "BOT STANDBY"
    db_class = "status-dot-green" if db_connected else "status-dot-red"
    db_text = "DB CONNECTED" if db_connected else "DB ERROR"
    
    st.markdown(f"""
        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); min-height: 98px; display: flex; flex-direction: column; justify-content: center; gap: 12px; margin-bottom: 16px;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>System</span>
                <div style='display: flex; align-items: center; gap: 6px;'><div class='{db_class}'></div><span style='font-size: 0.7rem; font-weight: 800; color: #64748B;'>{db_text}</span></div>
            </div>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>Engine</span>
                <div style='display: flex; align-items: center; gap: 6px;'><div class='{bot_class}'></div><span style='font-size: 0.7rem; font-weight: 800; color: #64748B;'>{bot_text}</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

# --- ASYMMETRICAL LAYOUT (70/30) ---
left_col, right_col = st.columns([7, 3], gap="large")

with left_col:
    st.markdown("<h3 style='margin: 0 0 16px 0; font-size: 1.2rem; color: #0F172A;'>Application Modules</h3>", unsafe_allow_html=True)
    
    # 3x2 Grid for Modules
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #EFF6FF; color: #3B82F6; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Inventory Adjustment</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Singkronisasi & rekonsiliasi data stok fisik vs sistem</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_inv", width="stretch"): st.switch_page("pages/1_inventory_adjustment.py")
    
    with r1c2:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #F3E8FF; color: #9333EA; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Sales Extract</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Otomatisasi penarikan faktur penjualan distributor</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_sales", width="stretch"): st.switch_page("pages/2_sales_extraction.py")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #DCFCE7; color: #16A34A; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Promo Compare</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Audit & komparasi data klaim promosi berjalan</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_promo", width="stretch"): st.switch_page("pages/3_promotion_comparison.py")
    
    with r2c2:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #FEF3C7; color: #D97706; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 16 16 12 12 8"></polyline><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Stock Mutation</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Lacak riwayat pergerakan stok harian (masuk/keluar)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_mut", width="stretch"): st.switch_page("pages/4_stock_mutation.py")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #FEE2E2; color: #DC2626; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v18H3zM15 9l-6 6M9 9l6 6"/></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Clearance Stock</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Monitor barang clearance dan sisa stok mati</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_clear", width="stretch"): st.switch_page("pages/5_clearance_stock.py")
    
    with r3c2:
        with st.container(border=True):
            st.markdown("""
            <div style='display: flex; gap: 12px; margin-bottom: 12px; min-height: 76px;'>
                <div style='width: 40px; height: 40px; border-radius: 8px; background: #E0E7FF; color: #4F46E5; display: flex; align-items: center; justify-content: center;'>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                </div>
                <div>
                    <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A;'>Initial Stock</h4>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 500; display: block; line-height: 1.3;'>Setup baseline data stok awal untuk distributor baru</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Launch Module", key="btn_init", width="stretch"): st.switch_page("pages/6_initial_stock.py")

with right_col:
    st.markdown("<h3 style='margin: 0 0 16px 0; font-size: 1.2rem; color: #0F172A;'>Recent Activity</h3>", unsafe_allow_html=True)
    
    with st.container(height=492, border=True):
        
        if db_connected:
            from datetime import timezone, timedelta
            df_adj, df_ext = load_historical_logs(supabase)
            unified_rows = []
            
            if not df_adj.empty:
                for _, row in df_adj.head(10).iterrows():
                    q = str(row.get("qty", ""))
                    mod = "Mutation" if ("PAC:" in q or "CAR:" in q) else "Inventory"
                    dist = user_to_dist.get(row.get("np_user", ""), row.get("np_user", "N/A"))
                    unified_rows.append({"ts": row["created_at"], "dist": dist, "mod": mod, "status": row.get("status"), "by": row.get("run_by") or row.get("np_user")})
            
            if not df_ext.empty:
                for _, row in df_ext.head(10).iterrows():
                    st_val = str(row.get("status", "Success"))
                    mod = "Sales" if "(Sales)" in st_val else "Inventory"
                    clean_status = st_val.replace(" (Sales)", "").strip()
                    unified_rows.append({"ts": row["created_at"], "dist": row.get("distributor_name", "N/A"), "mod": mod, "status": clean_status, "by": row.get("extracted_by")})
                    
            unified_rows.sort(key=lambda x: x["ts"], reverse=True)
            unified_rows = unified_rows[:6] # Only show top 6 in timeline
            
            if unified_rows:
                tl_html = "<div style='margin-left: 8px;'>"
                for r in unified_rows:
                    try:
                        t = r["ts"]
                        if t.tzinfo:
                            ts_str = t.tz_convert('Asia/Jakarta').strftime("%H:%M - %b %d")
                        else:
                            ts_str = (t + timedelta(hours=7)).strftime("%H:%M - %b %d")
                    except: ts_str = str(r["ts"])[:16]
                    
                    st_val = str(r["status"])
                    col = "#10B981" if st_val == "Success" else ("#EF4444" if st_val in ["Failed","Invalid"] else "#F59E0B")
                    
                    tl_html += (
                        "<div class='timeline-item'>"
                        f"<span class='timeline-date'>{ts_str}</span>"
                        f"<div class='timeline-title'>{html.escape(r['dist'])}</div>"
                        "<div class='timeline-desc'>"
                        f"<span style='color: {col}; font-weight: 700;'>{html.escape(st_val)}</span> in {r['mod']} by {html.escape(str(r['by']))}"
                        "</div>"
                        "</div>"
                    )
                tl_html += "</div>"
                st.markdown(tl_html, unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.8rem; color: #94A3B8;'>No recent activity.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 0.8rem; color: #EF4444;'>Database disconnected.</p>", unsafe_allow_html=True)

# Full Report Table still at the bottom
if db_connected:
    st.markdown("<div style='margin-top: 48px; border-top: 1px solid #E2E8F0; padding-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin: 0 0 16px 0; font-size: 1.2rem; color: #0F172A;'>Full Activity Report</h3>", unsafe_allow_html=True)
    
    col_filter, _ = st.columns([1.5, 2.5])
    with col_filter:
        period_option = st.selectbox("Reporting Period", ["Today", "Last 7 Days", "Last 30 Days", "All Time"], index=2, key="dashboard_report_period")
        
    now_utc = datetime.now(timezone.utc)
    if period_option == "Today": cutoff_date = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_option == "Last 7 Days": cutoff_date = now_utc - timedelta(days=7)
    elif period_option == "Last 30 Days": cutoff_date = now_utc - timedelta(days=30)
    else: cutoff_date = None
    
    # Process the large table exactly as before, with updated styling
    full_rows = []
    if not df_adj.empty:
        f_adj = df_adj[df_adj["created_at"] >= cutoff_date] if cutoff_date else df_adj.copy()
        for _, row in f_adj.iterrows():
            q = str(row.get("qty", ""))
            mod = "Stock Mutation" if ("PAC:" in q or "CAR:" in q) else "Inventory Adjustment"
            dist = user_to_dist.get(row.get("np_user", ""), row.get("np_user", "N/A"))
            full_rows.append({"ts": row["created_at"], "dist": dist, "mod": mod, "status": row.get("status", "N/A"), "by": row.get("run_by") or row.get("np_user", "N/A")})
    if not df_ext.empty:
        f_ext = df_ext[df_ext["created_at"] >= cutoff_date] if cutoff_date else df_ext.copy()
        for _, row in f_ext.iterrows():
            full_rows.append({"ts": row["created_at"], "dist": row.get("distributor_name", "N/A"), "mod": "Sales Extraction", "status": row.get("status", "N/A"), "by": row.get("extracted_by", "N/A")})
            
    full_rows.sort(key=lambda x: x["ts"], reverse=True)
    full_rows = full_rows[:30]
    
    if full_rows:
        tbl = ""
        for r in full_rows:
            try:
                t = r["ts"]
                ts_str = t.tz_convert('Asia/Jakarta').strftime("%Y-%m-%d %H:%M:%S") if t.tzinfo else (t + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            except: ts_str = str(r["ts"])[:19]
            
            s_val = str(r["status"])
            if s_val == "Success": s_col, s_bg = "#10B981", "rgba(16,185,129,0.1)"
            elif s_val in ["Failed","Invalid"]: s_col, s_bg = "#EF4444", "rgba(239,68,68,0.1)"
            else: s_col, s_bg = "#F59E0B", "rgba(245,158,11,0.1)"
            sb = f"<span style='background: {s_bg}; color: {s_col}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid {s_col}33; display: inline-block; white-space: nowrap;'>{html.escape(s_val.upper())}</span>"
            
            mod = r["mod"]
            mc = {"Inventory Adjustment": ("#0068C9", "rgba(0,104,201,0.08)"), "Sales Extraction": ("#7C3AED", "rgba(124,58,237,0.08)"), "Stock Mutation": ("#D97706", "rgba(217,119,6,0.08)"), "Promotion Comparison": ("#059669", "rgba(5,150,105,0.08)"), "Clearance Stock": ("#DC2626", "rgba(220,38,38,0.08)"), "Initial Stock": ("#6366F1", "rgba(99,102,241,0.08)")}
            m_col, m_bg = mc.get(mod, ("#808495", "rgba(128,132,149,0.08)"))
            mb = f"<span style='background: {m_bg}; color: {m_col}; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; border: 1px solid {m_col}33; display: inline-block; white-space: nowrap;'>{html.escape(mod)}</span>"
            
            tbl += f"<tr><td style='white-space:nowrap;'>{ts_str}</td><td>{html.escape(str(r['dist']))}</td><td>{mb}</td><td style='text-align:center;'>{sb}</td><td><code>{html.escape(str(r['by']))}</code></td></tr>"
            
        st.markdown(clean_html(f"<div class='table-container'><table class='custom-table'><thead><tr><th>Timestamp</th><th>Distributor</th><th>Module</th><th style='text-align:center;'>Status</th><th>Run By</th></tr></thead><tbody>{tbl}</tbody></table></div>"), unsafe_allow_html=True)
    else:
        st.info("No execution records found.")

render_footer()
