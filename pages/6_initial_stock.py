import time
import pandas as pd
import streamlit as st
import database
import playwright_engine
from utils import (
    make_solid_box, make_success_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state, render_wakelock, style_status,
)
from utils.theme import load_theme

# --- AUTH CHECK ---
check_auth()

# --- Load Theme (in case page is accessed directly) ---
load_theme()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
REASON_CODE = _sys_cfg["REASON_CODE"]
WAREHOUSE   = _sys_cfg["WAREHOUSE"]
URL_LOGIN   = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS  = _sys_cfg["TIMEOUT_MS"]
TABLE_UPDATE_INTERVAL = _sys_cfg["TABLE_UPDATE_INTERVAL"]

# --- STATE MANAGEMENT ---
init_session_state(
    initial_stock_df=None,
    initial_stock_raw=None,
    is_bot_running=False,
)

render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_bot_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="INITIAL STOCK ENGINE")
render_header("Initial Stock", st.session_state.current_user)

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

    selected_distributor = st.selectbox("Pilih Distributor", list_dist, index=default_index, key="init_stock_dist")
    st.query_params.clear()
    st.query_params["d"] = encode_param(selected_distributor)
    bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
    if bot_user:
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("NP User ID", value=bot_user, disabled=True, key="init_stock_user")
        with c2:
            st.text_input("NP Password", value="********", type="password", disabled=True, key="init_stock_pass")

# --- STEP 1: UPLOAD FILE ---
st.markdown("<div class='box-np'>Upload Stock Data</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload file with SKU and Qty columns (csv, xlsx)",
    type=['csv', 'xlsx'],
    key="init_stock_file"
)

# Parse uploaded file into raw dataframe
if uploaded_file is not None and st.session_state.initial_stock_raw is None and st.session_state.initial_stock_df is None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file, dtype=str, on_bad_lines='skip')
        else:
            df_raw = pd.read_excel(uploaded_file, dtype=str)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        st.session_state.initial_stock_raw = df_raw
        st.rerun()
    except Exception as e:
        st.error(f"Failed to parse file: {e}")

# --- COLUMN SELECTION ---
if st.session_state.initial_stock_raw is not None and st.session_state.initial_stock_df is None:
    df_raw = st.session_state.initial_stock_raw
    cols = list(df_raw.columns)

    st.markdown("<div class='box-review'>Map Columns</div>", unsafe_allow_html=True)
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        # Auto-detect SKU column
        sku_default = next((i for i, c in enumerate(cols) if c.lower() in ['sku', 'kode', 'product code', 'item code', 'code']), 0)
        sel_sku = st.selectbox("SKU Column", cols, index=sku_default, key="init_sel_sku")
    with mc2:
        # Auto-detect Qty column
        qty_default = next((i for i, c in enumerate(cols) if c.lower() in ['stokakhir', 'qty', 'quantity', 'stock', 'pcs', 'stokawal', 'stok']), 0)
        sel_qty = st.selectbox("Qty Column", cols, index=qty_default, key="init_sel_qty")
    with mc3:
        # Optional description column
        desc_options = ['(None)'] + cols
        desc_default = next((i + 1 for i, c in enumerate(cols) if any(p in c.lower() for p in ['merek', 'desc', 'name', 'variant', 'nama'])), 0)
        sel_desc = st.selectbox("Description Column (optional)", desc_options, index=desc_default, key="init_sel_desc")

    # Preview raw data
    with st.expander("Preview raw data", expanded=False):
        st.dataframe(df_raw.head(20), width="stretch", height=300, hide_index=True)

    if st.button("Confirm & Load Data", type="primary", width="stretch"):
        df_init = df_raw[[sel_sku, sel_qty]].copy()
        has_desc = sel_desc != '(None)' and sel_desc != sel_sku
        if has_desc:
            df_init[sel_desc] = df_raw[sel_desc]

        # Rename columns
        new_cols = ['SKU', 'Qty']
        if has_desc:
            new_cols.append('Description')
        df_init.columns = new_cols

        # Clean data
        df_init = df_init.dropna(subset=['SKU'])
        df_init['SKU'] = df_init['SKU'].astype(str).str.strip()
        df_init = df_init[~df_init['SKU'].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]
        df_init['Qty'] = pd.to_numeric(
            df_init['Qty'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        ).fillna(0).astype(int)

        # Filter out zero qty
        df_init = df_init[df_init['Qty'] != 0].reset_index(drop=True)

        if 'Description' not in df_init.columns:
            df_init['Description'] = ''

        st.session_state.initial_stock_df = df_init
        st.session_state.initial_stock_raw = None
        st.rerun()

# --- REVIEW UPLOADED DATA ---
if st.session_state.initial_stock_df is not None:
    df_init = st.session_state.initial_stock_df

    st.markdown(make_solid_box(f"Loaded — {len(df_init)} items from uploaded file", "#3b82f6", "#3b82f6"), unsafe_allow_html=True)

    if st.button("Clear uploaded data", width="stretch"):
        st.session_state.initial_stock_df = None
        st.session_state.initial_stock_raw = None
        st.rerun()

# --- REVIEW TABLE ---
if st.session_state.initial_stock_df is not None and len(st.session_state.initial_stock_df) > 0:
    df_init = st.session_state.initial_stock_df

    # Summary metrics
    sm1, sm2 = st.columns(2)
    with sm1:
        st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Total SKU</div><div class="metric-value">{len(df_init)}</div></div>''', unsafe_allow_html=True)
    with sm2:
        total_qty = df_init['Qty'].sum()
        st.markdown(f'''<div class="metric-box-mismatch"><div class="metric-label">Total Qty</div><div class="metric-value">{total_qty:,}</div></div>''', unsafe_allow_html=True)

    st.markdown("<div class='box-review'>Initial Stock Review</div>", unsafe_allow_html=True)

    # Show review table
    df_display = df_init.copy()
    display_cols = ['SKU', 'Description', 'Qty'] if 'Description' in df_display.columns else ['SKU', 'Qty']
    st.dataframe(style_status(df_display[display_cols]), width="stretch", height=400, hide_index=True)

    # --- EXECUTE ---
    if st.session_state.is_bot_running:
        st.markdown("<div style='text-align: center; padding: 8px; color: #a3a3a3; font-size: 0.85rem; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif;'>⏳ Initializing stock data...</div>", unsafe_allow_html=True)
    else:
        if st.button("EXECUTE INITIAL STOCK", type="primary", width="stretch"):
            if not bot_user or not bot_pass:
                st.error("Kredensial tidak ditemukan!")
            else:
                st.session_state.is_bot_running = True
                st.rerun()

# --- PENDING EXECUTION (after rerun hides button) ---
if st.session_state.is_bot_running and st.session_state.initial_stock_df is not None:
    df_init = st.session_state.initial_stock_df

    # Build execution DataFrame (positive qty for initial stock)
    df_exec = df_init[['SKU', 'Qty']].copy()
    df_exec['Status'] = 'Pending'
    df_exec['Keterangan'] = 'Ready to Input'

    st.markdown("<div class='box-queue'>Initial Stock Execution</div>", unsafe_allow_html=True)
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
    st.session_state.initial_stock_df = None

render_footer()
