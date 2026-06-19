import time
import pandas as pd
import streamlit as st
import database
import playwright_engine
from utils import (
    make_solid_box, make_success_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state, render_wakelock, style_status, render_aggrid,
)

# --- AUTH CHECK ---
check_auth()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
REASON_CODE = _sys_cfg["REASON_CODE"]
WAREHOUSE   = _sys_cfg["WAREHOUSE"]
URL_LOGIN   = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS  = _sys_cfg["TIMEOUT_MS"]
TABLE_UPDATE_INTERVAL = _sys_cfg["TABLE_UPDATE_INTERVAL"]

# --- STATE MANAGEMENT ---
init_session_state(
    clearance_df=None,
    is_bot_running=False,
    prev_clearance_file=None,
)

render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_bot_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="CLEARANCE ENGINE")
render_header("Clearance Stock", st.session_state.current_user)

# --- DISTRIBUTOR SELECTION ---
with st.container(border=True):
    st.markdown("<div class='box-np'>Target Distributor</div>", unsafe_allow_html=True)
    list_dist = database.get_distributor_list(supabase)

    url_d = st.query_params.get("d", None)
    url_dist = None
    if url_d:
        url_dist = decode_param(url_d)
    else:
        plain_dist = st.query_params.get("distributor", None)
        if plain_dist:
            url_dist = plain_dist
            st.query_params.pop("distributor", None)

    default_index = list_dist.index(url_dist) if url_dist in list_dist else 0

    selected_distributor = st.selectbox("Pilih Distributor", list_dist, index=default_index, key="clearance_dist")
    st.query_params.clear()
    st.query_params["d"] = encode_param(selected_distributor)
    bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
    if bot_user:
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("NP User ID", value=bot_user, disabled=True, key="clearance_user")
        with c2:
            st.text_input("NP Password", value="********", type="password", disabled=True, key="clearance_pass")

# --- STEP 1: EXTRACT ---
ext_label_placeholder = st.empty()
ext_log_placeholder = st.empty()

btn_label = "Extracting..." if st.session_state.is_bot_running else "Step 1: Extract Real-time Stock from Newspage"
extract_btn = st.button(btn_label, type="primary", width="stretch", disabled=st.session_state.is_bot_running or not bot_user)

if extract_btn:
    if not bot_user or not bot_pass:
        st.error("Kredensial untuk distributor ini tidak ditemukan.")
        st.stop()

    st.session_state.is_bot_running = True
    ext_label_placeholder.markdown(f"""
        <div style='display: inline-block; margin-bottom: 4px;'>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>System Activity</span>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #e5e5e5; text-transform: uppercase; letter-spacing: 0.1em;'>EXTRACT_LOG</span>
        </div>
    """, unsafe_allow_html=True)
    ext_logs_history = []
    ext_last_log_time = [time.time()]

    def ext_ui_log(module, msg):
        now = time.time(); diff_ms = int((now - ext_last_log_time[0]) * 1000); ext_last_log_time[0] = now
        from datetime import datetime, timezone, timedelta
        timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
        tag_class = f"tag-{module.lower()}"
        ext_logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
        render_terminal(ext_log_placeholder, ext_logs_history)

    playwright_engine.run_extract(
        bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
        ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user
    )

# --- REVIEW EXTRACTED DATA ---
if st.session_state.clearance_df is not None:
    st.markdown(make_solid_box(f"Extracted — {len(st.session_state.clearance_df)} items loaded from server", "#3b82f6", "#3b82f6"), unsafe_allow_html=True)
    if st.button("Clear extracted data", width="stretch"):
        st.session_state.clearance_df = None
        st.rerun()

# After extraction, the run_extract stores data in st.session_state.np_df
# We need to convert it to clearance format (all qty as negative)
if st.session_state.get("np_df") is not None and st.session_state.clearance_df is None:
    np_df = st.session_state.np_df.copy()
    np_df.columns = [str(c).strip() for c in np_df.columns]

    # Identify Product Code and Stock columns
    sku_col = next((c for c in np_df.columns if 'product code' in c.lower()), None)
    qty_col = next((c for c in np_df.columns if 'stock' in c.lower() and 'available' in c.lower()), None)
    if not qty_col:
        qty_col = next((c for c in np_df.columns if 'stock' in c.lower() or 'qty' in c.lower()), None)
    desc_col = next((c for c in np_df.columns if 'product' in c.lower() and ('desc' in c.lower() or 'name' in c.lower())), None)

    if sku_col and qty_col:
        df_clear = np_df[[sku_col, qty_col]].copy()
        if desc_col and desc_col != sku_col:
            df_clear[desc_col] = np_df[desc_col]
        df_clear.columns = ['SKU', 'Qty'] + (['Description'] if desc_col and desc_col != sku_col else [])

        # Clean data
        df_clear = df_clear.dropna(subset=['SKU'])
        df_clear['SKU'] = df_clear['SKU'].astype(str).str.split('.').str[0].str.strip()
        df_clear = df_clear[~df_clear['SKU'].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]
        df_clear['Qty'] = pd.to_numeric(
            df_clear['Qty'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        ).fillna(0).astype(int)

        # Filter out zero stock
        df_clear = df_clear[df_clear['Qty'] != 0].reset_index(drop=True)

        if 'Description' not in df_clear.columns:
            df_clear['Description'] = ''

        # Store as clearance data
        st.session_state.clearance_df = df_clear
        # Clear np_df so it doesn't get re-processed
        st.session_state.np_df = None
        st.rerun()
    else:
        st.error(f"Could not identify Product Code or Stock columns. Found: {list(np_df.columns)}")

# --- REVIEW TABLE ---
if st.session_state.clearance_df is not None and len(st.session_state.clearance_df) > 0:
    df_clear = st.session_state.clearance_df

    # Summary metrics
    sm1, sm2 = st.columns(2)
    with sm1:
        st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Total SKU to Clear</div><div class="metric-value">{len(df_clear)}</div></div>''', unsafe_allow_html=True)
    with sm2:
        st.markdown(f'''<div class="metric-box-mismatch"><div class="metric-label">Total SKU to Process</div><div class="metric-value">{len(df_clear)}</div></div>''', unsafe_allow_html=True)

    st.markdown("<div class='box-review'>Stock Clearance Review</div>", unsafe_allow_html=True)

    # Show review table with negative qty preview
    df_display = df_clear.copy()
    df_display['Clear Qty'] = df_display['Qty'].apply(lambda x: f"-{abs(x)}")
    display_cols = ['SKU', 'Description', 'Qty', 'Clear Qty'] if 'Description' in df_display.columns else ['SKU', 'Qty', 'Clear Qty']
    render_aggrid(df_display[display_cols], key="clearance_review", enable_filters=True)

    # --- EXECUTE ---
    if st.button("EXECUTE CLEARANCE", type="primary", width="stretch"):
        if not bot_user or not bot_pass:
            st.error("Kredensial tidak ditemukan!")
        else:
            st.session_state.is_bot_running = True

            # Build execution DataFrame (negative qty for clearance)
            df_exec = df_clear[['SKU', 'Qty']].copy()
            df_exec['Qty'] = '-' + df_exec['Qty'].astype(str)
            df_exec['Status'] = 'Pending'
            df_exec['Keterangan'] = 'Ready to Clear'

            st.markdown("<div class='box-queue'>Clearance Execution</div>", unsafe_allow_html=True)
            table_placeholder = st.empty()
            table_placeholder.dataframe(style_status(df_exec), width="stretch", height=400, hide_index=True)

            log_label_placeholder = st.empty()
            log_placeholder = st.empty()

            log_label_placeholder.markdown(f"""
                <div style='display: inline-block; margin-bottom: 4px;'>
                    <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #f87171; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                    <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #e5e5e5; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                </div>
            """, unsafe_allow_html=True)

            bot_logs_history = []
            bot_last_log_time = [time.time()]

            def bot_ui_log(module, msg):
                now = time.time(); diff_ms = int((now - bot_last_log_time[0]) * 1000); bot_last_log_time[0] = now
                from datetime import datetime, timezone, timedelta
                timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
                tag_class = f"tag-{module.lower()}"
                bot_logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
                render_terminal(log_placeholder, bot_logs_history)

            playwright_engine.run_execution(
                df_exec, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
                REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase
            )

            # Clear state after execution
            st.session_state.clearance_df = None

render_footer()
