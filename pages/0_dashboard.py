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
# --- HEADER ---
col1, col2 = st.columns([0.85, 0.15])
with col1:
    render_header("Automation Tool", st.session_state.current_user)
with col2:
    st.markdown("""
        <style>
            .neo-modal-overlay-signout {
                display: none;
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15, 23, 42, 0.7);
                z-index: 999998;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(4px);
            }
            
            #signout-modal-toggle { display: none; }
            #signout-modal-toggle:checked ~ .neo-modal-overlay-signout { display: flex; }
            
            .neo-btn-signout {
                background-color: #0068C9; color: #FFFFFF; border: 2px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 0px; font-family: 'Source Sans 3', sans-serif; font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1); display: flex; align-items: center; justify-content: center; width: 100%; height: 41px; box-sizing: border-box;
            }
            .neo-btn-signout:hover {
                transform: translate(2px, 2px); box-shadow: 4px 4px 0px 0px #0F172A;
            }
            .neo-btn-signout:active {
                transform: translate(4px, 4px); box-shadow: 2px 2px 0px 0px #0F172A;
            }
            
            /* Hide Streamlit button initially */
            div.element-container:has(#neo-signout-marker) + div.element-container {
                display: none;
                position: fixed;
                z-index: 999999;
                top: 50%;
                left: 50%;
                margin-top: 93px;
                margin-left: 8px;
            }
            
            /* Show Streamlit button when modal is open */
            div.element-container:has(#signout-modal-toggle:checked) + div.element-container {
                display: block !important;
            }
            /* Style the Streamlit button to match neo-brutalism */
            div.element-container:has(#neo-signout-marker) + div.element-container {
                width: 180px !important;
            }
            div.element-container:has(#neo-signout-marker) + div.element-container button,
            div.element-container:has(#neo-signout-marker) + div.element-container button:hover,
            div.element-container:has(#neo-signout-marker) + div.element-container button:active {
                background-color: #E63946 !important;
                color: #FFFFFF !important;
                height: 44px !important;
                min-height: 44px !important;
                max-height: 44px !important;
                width: 180px !important;
                min-width: 180px !important;
                max-width: 180px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: 3px solid #0F172A !important;
                border-radius: 0 !important;
                box-shadow: 4px 4px 0px 0px #0F172A !important;
                padding: 0 !important;
                margin: 0 !important;
                box-sizing: border-box !important;
                transform: none !important;
            }
            div.element-container:has(#neo-signout-marker) + div.element-container button p {
                font-size: 1rem !important;
                font-weight: 800 !important;
                color: #FFFFFF !important;
                margin: 0 !important;
                padding: 0 !important;
                line-height: 1 !important;
            }
            div.element-container:has(#neo-signout-marker) + div.element-container button:hover {
                transform: translate(2px, 2px) !important;
                box-shadow: 2px 2px 0px 0px #0F172A !important;
            }
            div.element-container:has(#neo-signout-marker) + div.element-container button:active {
                transform: translate(4px, 4px) !important;
                box-shadow: 0px 0px 0px 0px #0F172A !important;
            }
        </style>
        <div id="neo-signout-marker" style="display: none;"></div>
        <div style="display: flex; justify-content: center; width: 100%; margin-bottom: 0px; margin-top: 14px;">
            <label for="signout-modal-toggle" class="neo-btn-signout">Sign Out</label>
        </div>
        <input type="checkbox" id="signout-modal-toggle" />
        <div class="neo-modal-overlay-signout">
            <div style="background: #FFFFFF; border: 4px solid #0F172A; box-shadow: 12px 12px 0px 0px #0F172A; padding: 32px; max-width: 450px; width: 90%; height: 350px; text-align: center; position: relative; box-sizing: border-box;">
                <div style="background: #E63946; width: 64px; height: 64px; margin: -72px auto 24px auto; border: 4px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; display: flex; align-items: center; justify-content: center;">
                    <svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='#FFFFFF' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'></path><polyline points='16 17 21 12 16 7'></polyline><line x1='21' y1='12' x2='9' y2='12'></line></svg>
                </div>
                <h3 style="font-family: 'Source Sans 3', sans-serif; font-weight: 900; font-size: 1.5rem; color: #0F172A; margin-bottom: 8px; margin-top: 0; text-transform: uppercase;">Are you absolutely sure?</h3>
                <p style='color: #475569; font-weight: 700; font-size: 0.95rem; margin-top: 0; margin-bottom: 24px;'>This action cannot be undone. This will end your current session and require you to sign in again.</p>
                <label for="signout-modal-toggle" style="background: #F1F5F9; color: #0F172A; font-family: 'Source Sans 3', sans-serif; font-weight: 800; font-size: 1rem; padding: 0px; width: 180px; height: 44px; display: inline-flex; align-items: center; justify-content: center; border: 3px solid #0F172A; cursor: pointer; text-transform: uppercase; box-shadow: 4px 4px 0px 0px #0F172A; transition: all 0.1s ease; box-sizing: border-box; position: absolute; right: 50%; margin-right: 8px; top: 265px;">Cancel</label>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    def signout_callback():
        st.session_state.logged_in = False
        st.session_state.current_user = "unknown"
        st.session_state.logout_requested = True
        st.session_state.ignore_cookie = True

    st.button("CONFIRM", key="signout_confirm_hidden", on_click=signout_callback, use_container_width=True)

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
<div style='background: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: clamp(16px, 4vw, 32px); margin-bottom: 32px; margin-top: 16px;'>
    <div style='display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;'>
        <div style='background: #0068C9; color: #FFFFFF; padding: 6px 16px; font-weight: 800; font-size: 0.85rem; border: 2px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; letter-spacing: 0.05em;'>AUTOMATION TOOL</div>
        <div style='pointer-events: none; display: inline-flex; align-items: center; background: #FFFFFF; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; padding: 4px 12px; gap: 6px;'>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>SESSION:</span>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 900; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em;'>{html.escape(st.session_state.current_user).upper()}</span>
        </div>
    </div>
    <h1 style='font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 900; color: #0F172A; margin: 0; line-height: 1.1; letter-spacing: -0.02em; word-wrap: break-word;'>HALO, {html.escape(st.session_state.current_user).upper()}! 👋</h1>
    <p style='font-size: clamp(0.85rem, 2vw, 1.05rem); color: #0F172A; margin-top: 16px; margin-bottom: 0; font-weight: 700; border-top: 3px solid #0F172A; padding-top: 12px; display: block; text-transform: uppercase;'>PANTAU RINGKASAN AKTIVITAS OTOMATISASI DISTRIBUTOR ANDA HARI INI, {datetime.now().strftime('%d %b %Y').upper()}.</p>
</div>
""", unsafe_allow_html=True)

# --- TOP KPI METRICS ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(render_metric_card("Total Extractions", total_extractions), unsafe_allow_html=True)
with m2:
    st.markdown(render_metric_card("Active Distributors", total_distributors), unsafe_allow_html=True)
with m3:
    st.markdown(render_metric_card("Synced Logs", total_logs), unsafe_allow_html=True)
with m4:
    bot_class = "status-dot-green" if bot_running else "status-dot-gray"
    bot_text = "BOT RUNNING" if bot_running else "BOT STANDBY"
    db_class = "status-dot-green" if db_connected else "status-dot-red"
    db_text = "DB CONNECTED" if db_connected else "DB ERROR"
    
    st.markdown(clean_html(f"""
        <div style='background-color: #FFFFFF; padding: 20px 24px; border-radius: 0px; box-shadow: 6px 6px 0px 0px #0F172A; display: flex; flex-direction: column; justify-content: center; border: 3px solid #0F172A; margin-bottom: 16px; width: 100%; height: 125px; box-sizing: border-box; font-family: "Source Sans 3", "Source Sans Pro", sans-serif; gap: 12px;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>System</span>
                <div style='display: flex; align-items: center; gap: 6px;'><div class='{db_class}'></div><span style='font-size: 0.7rem; font-weight: 800; color: #64748B;'>{db_text}</span></div>
            </div>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>Engine</span>
                <div style='display: flex; align-items: center; gap: 6px;'><div class='{bot_class}'></div><span style='font-size: 0.7rem; font-weight: 800; color: #64748B;'>{bot_text}</span></div>
            </div>
        </div>
    """), unsafe_allow_html=True)

st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

# --- ASYMMETRICAL LAYOUT (70/30) ---
left_col, right_col = st.columns([7, 3], gap="large")

with left_col:
    st.markdown("<div style='margin: 0 0 16px 0; font-size: 1.05rem; color: #0F172A; background-color: #F1F5F9; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; padding: 6px 12px; display: inline-block; font-weight: 900; text-transform: uppercase; line-height: 1.2; letter-spacing: 0.05em;'>Application Modules</div>", unsafe_allow_html=True)
    
    MODULES = [
        {"title": "Inventory Adjustment", "desc": "Singkronisasi & rekonsiliasi data stok fisik vs sistem", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'></path><polyline points='3.27 6.96 12 12.01 20.73 6.96'></polyline><line x1='12' y1='22.08' x2='12' y2='12'></line></svg>", "bg": "#EFF6FF", "color": "#3B82F6", "page": "pages/1_inventory_adjustment.py", "key": "btn_inv"},
        {"title": "Sales Extract", "desc": "Otomatisasi penarikan faktur penjualan distributor", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='3' width='20' height='14' rx='2' ry='2'></rect><line x1='8' y1='21' x2='16' y2='21'></line><line x1='12' y1='17' x2='12' y2='21'></line></svg>", "bg": "#F3E8FF", "color": "#9333EA", "page": "pages/2_sales_extraction.py", "key": "btn_sales"},
        {"title": "Promo Compare", "desc": "Audit & komparasi data klaim promosi berjalan", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path><polyline points='14 2 14 8 20 8'></polyline><line x1='16' y1='13' x2='8' y2='13'></line><line x1='16' y1='17' x2='8' y2='17'></line><polyline points='10 9 9 9 8 9'></polyline></svg>", "bg": "#DCFCE7", "color": "#16A34A", "page": "pages/3_promotion_comparison.py", "key": "btn_promo"},
        {"title": "Stock Mutation", "desc": "Lacak riwayat pergerakan stok harian (masuk/keluar)", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><polyline points='12 16 16 12 12 8'></polyline><line x1='8' y1='12' x2='16' y2='12'></line></svg>", "bg": "#FEF3C7", "color": "#D97706", "page": "pages/4_stock_mutation.py", "key": "btn_mut"},
        {"title": "Clearance Stock", "desc": "Monitor barang clearance dan sisa stok mati", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M3 3h18v18H3zM15 9l-6 6M9 9l6 6'/></svg>", "bg": "#FEE2E2", "color": "#DC2626", "page": "pages/5_clearance_stock.py", "key": "btn_clear"},
        {"title": "Initial Stock", "desc": "Setup baseline data stok awal untuk distributor baru", "icon": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='12' y1='8' x2='12' y2='16'></line><line x1='8' y1='12' x2='16' y2='12'></line></svg>", "bg": "#E0E7FF", "color": "#4F46E5", "page": "pages/6_initial_stock.py", "key": "btn_init"},
    ]
    
    for i in range(0, len(MODULES), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(MODULES):
                mod = MODULES[i + j]
                with col:
                    with st.container():
                        st.markdown(f"""
                        <span class='neo-module-card-marker' style='display:none;'></span>
                            <div style='display: flex; gap: 16px; margin-bottom: 16px; align-items: center; padding: 12px 16px 0px 16px;'>
                            <div style='width: 44px; height: 44px; border-radius: 0px; background: {mod["color"]}; color: #FFFFFF; display: flex; align-items: center; justify-content: center; border: 3px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; flex-shrink: 0;'>
                                {mod["icon"]}
                            </div>
                            <div style='flex: 1;'>
                                <h4 style='margin: 0; font-size: 1.05rem; color: #0F172A; font-weight: 900; letter-spacing: -0.5px; text-transform: uppercase;'>{mod["title"]}</h4>
                                <span style='font-size: 0.75rem; color: #0F172A; font-weight: 700; display: block; line-height: 1.3; margin-top: 2px;'>{mod["desc"]}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Launch Module", key=mod["key"], use_container_width=True): st.switch_page(mod["page"])
        if i < len(MODULES) - 2:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

with right_col:
    rc1, rc2 = st.columns([6, 4])
    with rc1:
        st.markdown("<div style='margin: 0 0 16px 0; font-size: 1.05rem; color: #0F172A; background-color: #F1F5F9; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; padding: 6px 12px; display: inline-block; font-weight: 900; text-transform: uppercase; line-height: 1.2; letter-spacing: 0.05em;'>Recent Activity</div>", unsafe_allow_html=True)
    with rc2:
        if st.button("Ping", use_container_width=True, key="ping_newspage"):
            import requests
            import re
            import time
            try:
                cfg = database.get_system_config(supabase)
                url = cfg.get("URL_LOGIN", "")
                bot_user = st.secrets.get("NP_USER_SUPER", "")
                bot_pass = st.secrets.get("NP_PASS_SUPER", "")
                
                if not url or not bot_user or not bot_pass:
                    st.toast("Missing URL/Credentials", icon=":material/error:")
                else:
                    st.toast("Initiating ping test...", icon=":material/hourglass_empty:")
                    start_t = time.time()
                    
                    import subprocess
                    from playwright_engine import ensure_playwright
                    try:
                        ensure_playwright()
                    except Exception as e:
                        st.toast(f"Failed to install browser dependencies: {e}", icon=":material/error:")
                    script = f"""
import asyncio, time
from playwright.async_api import async_playwright
async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('{url}', wait_until='domcontentloaded')
            await page.fill('id=txtUserid', '{bot_user}')
            await page.fill('id=txtPasswd', '{bot_pass}')
            await page.click('id=btnLogin', force=True)
            
            start_wait = time.time()
            while time.time() - start_wait < 15.0:
                if 'Default.aspx' in page.url:
                    break
                try:
                    btn = page.locator('id=SYS_ASCX_btnContinue')
                    if await btn.is_visible():
                        await btn.click(force=True)
                        # Wait a little for navigation to start
                        await page.wait_for_timeout(2000)
                except:
                    pass
                await page.wait_for_timeout(500)
                
            final_url = page.url
            await browser.close()
            if 'Default.aspx' in final_url or 'Logon' not in final_url:
                print('OK')
            else:
                print('FAIL')
    except Exception as e:
        print('ERR: ' + str(e))
asyncio.run(main())
"""
                    try:
                        import sys
                        res = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=25)
                        elapsed = time.time() - start_t
                        out = res.stdout.strip()
                        err = res.stderr.strip()
                        if out == 'OK':
                            st.toast(f"Superuser Login OK ({elapsed:.1f}s)", icon=":material/check_circle:")
                        elif out == 'FAIL':
                            st.toast(f"Login Failed (Check Credentials)", icon=":material/warning:")
                        else:
                            st.toast(f"Ping err: {out} {err}", icon=":material/error:")
                    except subprocess.TimeoutExpired:
                        st.toast("Ping timeout", icon=":material/error:")
                    except Exception as e:
                        st.toast(f"Ping error: {e}", icon=":material/error:")
            except Exception as e:
                st.toast(f"Ping Failed: {e}", icon=":material/error:")
                
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        
        if db_connected:
            from datetime import timezone, timedelta
            df_adj, df_ext = load_historical_logs(supabase)
            unified_rows = []
            
            if not df_adj.empty:
                # Deduplicate multiple SKUs in the same batch
                f_adj_recent = df_adj.copy()
                f_adj_recent['time_key'] = f_adj_recent['created_at'].dt.floor('Min')
                f_adj_recent = f_adj_recent.drop_duplicates(subset=['np_user', 'run_by', 'time_key', 'status'])
                for _, row in f_adj_recent.head(10).iterrows():
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
            unified_rows = unified_rows[:5] # Only show top 5 in timeline to align perfectly with module rows
            
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
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 0 0 16px 0; font-size: 1.05rem; color: #0F172A; background-color: #F1F5F9; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; padding: 6px 12px; display: inline-block; font-weight: 900; text-transform: uppercase; line-height: 1.2; letter-spacing: 0.05em;'>Full Activity Report</div>", unsafe_allow_html=True)
    
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
        # Deduplicate multiple SKUs logged in the same minute for the same module
        f_adj['time_key'] = f_adj['created_at'].dt.floor('Min')
        f_adj = f_adj.drop_duplicates(subset=['np_user', 'run_by', 'time_key', 'status'])
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
            if s_val == "Success": s_bg = "#4ADE80"
            elif s_val in ["Failed","Invalid"]: s_bg = "#F87171"
            else: s_bg = "#FBBF24"
            sb = f"<span style='background: {s_bg}; color: #0F172A; padding: 4px 10px; border-radius: 0px; font-size: 0.75rem; font-weight: 800; border: 2px solid #0F172A; display: inline-block; white-space: nowrap; box-shadow: 2px 2px 0px 0px #0F172A; letter-spacing: 0.05em;'>{html.escape(s_val.upper())}</span>"
            
            mod = r["mod"]
            mc = {"Inventory Adjustment": "#4CC9F0", "Sales Extraction": "#FFDE59", "Stock Mutation": "#4ADE80", "Promotion Comparison": "#FF90E8", "Clearance Stock": "#FF9F1C", "Initial Stock": "#A78BFA"}
            m_bg = mc.get(mod, "#E2E8F0")
            mb = f"<span style='background: {m_bg}; color: #0F172A; padding: 4px 10px; border-radius: 0px; font-size: 0.75rem; font-weight: 800; border: 2px solid #0F172A; display: inline-block; white-space: nowrap; box-shadow: 2px 2px 0px 0px #0F172A;'>{html.escape(mod.upper())}</span>"
            
            rb = f"<span style='background: #FFFFFF; color: #0F172A; font-family: monospace; padding: 4px 8px; border: 2px solid #0F172A; font-size: 0.75rem; font-weight: 700; box-shadow: 2px 2px 0px 0px #0F172A;'>{html.escape(str(r['by']).upper())}</span>"
            tbl += f"<tr><td style='white-space:nowrap; font-weight: 600;'>{ts_str}</td><td>{html.escape(str(r['dist']))}</td><td>{mb}</td><td style='text-align:center;'>{sb}</td><td>{rb}</td></tr>"
            
        st.markdown(clean_html(f"<div class='table-container'><table class='custom-table'><thead><tr><th>Timestamp</th><th>Distributor</th><th>Module</th><th style='text-align:center;'>Status</th><th>Run By</th></tr></thead><tbody>{tbl}</tbody></table></div>"), unsafe_allow_html=True)
    else:
        st.info("No execution records found.")

render_footer()
