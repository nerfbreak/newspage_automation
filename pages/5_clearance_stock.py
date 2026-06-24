import pandas as pd
import streamlit as st
import database
import playwright_engine
import importlib
importlib.reload(playwright_engine)
from utils import (
    render_footer, make_solid_box, render_metric_card,
    check_auth, render_indicators, render_header,
    encode_param, send_telegram_alert,
    init_session_state, render_wakelock, style_status,
    make_terminal_logger,
    resolve_distributor_url, safe_parse_numeric,
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
    st.subheader("Target Distributor")
    list_dist = database.get_distributor_list(supabase)
    _, default_index = resolve_distributor_url(list_dist)

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

if st.session_state.is_bot_running:
    st.markdown(make_solid_box("Extracting stock data...", "#0068C9", "#0068C9"), unsafe_allow_html=True)
    extract_btn = False
else:
    extract_btn = st.button("Step 1: Extract Real-time Stock from Newspage", type="primary", width="stretch", disabled=not bot_user)

# Use pending flag so extraction starts AFTER rerun hides the button
if extract_btn:
    st.session_state._pending_clearance_extract = True
    st.session_state.is_bot_running = True
    st.rerun()

if st.session_state.get("_pending_clearance_extract", False):
    st.session_state._pending_clearance_extract = False
    if not bot_user or not bot_pass:
        st.error("Kredensial untuk distributor ini tidak ditemukan.")
        st.session_state.is_bot_running = False
        st.stop()

    st.session_state.is_bot_running = True
    ext_label_placeholder.markdown(f"""
        <div style='display: inline-block; margin-bottom: 4px;'>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>System Activity</span>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>EXTRACT_LOG</span>
        </div>
    """, unsafe_allow_html=True)
    ext_ui_log, _ = make_terminal_logger(ext_log_placeholder)

    playwright_engine.run_extract(
        bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
        ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user
    )

# --- REVIEW EXTRACTED DATA ---
if st.session_state.clearance_df is not None:
    st.markdown(make_solid_box(f"Extracted — {len(st.session_state.clearance_df)} items loaded from server", "#0068C9", "#0068C9"), unsafe_allow_html=True)
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
        
        # Apply SKU mapping rule
        TARGET_SKUS = database.get_target_skus(supabase)
        EXCLUDE_PREFIX = ['8021803', '8021804']
        df_clear['SKU'] = df_clear['SKU'].apply(lambda x: '0' + str(x) if (str(x) in TARGET_SKUS and str(x) not in EXCLUDE_PREFIX) else x)
        df_clear['Qty'] = df_clear['Qty'].apply(safe_parse_numeric).astype(int)

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
    st.markdown(render_metric_card("Total SKU to Clear", len(df_clear)), unsafe_allow_html=True)

    st.subheader("Stock Clearance Review")

    # Show review table with negative qty preview
    df_display = df_clear.copy()
    df_display['Clear Qty'] = -df_display['Qty'].abs()
    display_cols = ['SKU', 'Description', 'Qty', 'Clear Qty'] if 'Description' in df_display.columns else ['SKU', 'Qty', 'Clear Qty']
    st.dataframe(style_status(df_display[display_cols]), width="stretch", hide_index=True)

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

            st.subheader("Clearance Execution")
            table_placeholder = st.empty()
            table_placeholder.dataframe(style_status(df_exec), width="stretch", hide_index=True)

            log_label_placeholder = st.empty()
            log_placeholder = st.empty()

            log_label_placeholder.markdown(f"""
                <div style='display: inline-block; margin-bottom: 4px;'>
                    <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                    <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                </div>
            """, unsafe_allow_html=True)
            bot_ui_log, _ = make_terminal_logger(log_placeholder)

            playwright_engine.run_execution(
                df_exec, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
                REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase
            )

            # Clear state after execution
            st.session_state.clearance_df = None

render_footer()
